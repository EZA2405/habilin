import tempfile
import unittest
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from habilin.core import (EstateAgent, Principal, Rejected, digest, estate_tax, late_penalty, nominal_due_date,
                          uk_due_date, uk_inheritance_tax)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.agent = EstateAgent(Path(self.temp.name) / "case.db")
        self.owner = Principal("demo-owner", "owner", "EST-001")
        self.operator = Principal("demo-operator", "operator", "EST-001")
        self.professional = Principal("demo-cpa", "professional", "EST-001")
        self.agent.tool(self.operator, "answer_question", answer=False)

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_record_to_professional_review(self):
        result = self.agent.advance(self.operator)
        self.assertEqual(result["stage"], "await_professional")
        self.assertEqual(result["packet"]["tax_centavos"], 15_000_000)
        self.assertEqual(result["record"]["share_bps"], 5000)
        self.assertEqual(result["record"]["version"], 2)
        self.assertEqual([e["tool"] for e in result["events"]],
                         ["answer_question", "request_record", "resolve_record", "prepare_packet"])

    def approve(self):
        case = self.agent.advance(self.operator)
        packet_hash = digest(case["packet"])
        self.agent.tool(self.professional, "professional_approve", packet_hash=packet_hash, confirmed=True)
        code = self.agent.issue_code()
        self.agent.tool(self.owner, "owner_approve", packet_hash=packet_hash, confirmed=True, code=code)
        return packet_hash, code

    def mutate(self, fn):
        with self.agent.connection() as db:
            case = json.loads(db.execute("SELECT data FROM cases").fetchone()[0])
            fn(case)
            self.agent._save(db, case)

    def test_complete_case_preserves_unfinished_legal_steps(self):
        self.approve()
        self.assertEqual(self.agent.advance(self.operator)["stage"], "filing_unknown")
        case = self.agent.advance(self.operator)
        self.assertEqual(case["stage"], "payment_pending")
        self.assertIsNone(case["payment_receipt"])
        case = self.agent.advance(self.operator)
        self.assertEqual(case["stage"], "completed")
        self.assertEqual(case["balance_centavos"], 85_000_000)
        self.assertEqual(case["filing_receipt"], "SIM-FILE-0001")
        self.assertEqual(case["payment_receipt"], "SIM-PAY-0001")
        self.assertEqual(len(case["open_steps"]), 4)

    def test_close_case_deletes_personal_data_and_keeps_proof(self):
        packet_hash, _ = self.approve()
        for _ in range(3):
            self.agent.advance(self.operator)
        self.agent.tool(self.owner, "lock")  # a locked case can still be closed: deletion moves no money
        for principal in [self.operator, self.professional]:
            with self.subTest(principal=principal.role), self.assertRaises(Rejected):
                self.agent.tool(principal, "close_case", confirmed=True)
        with self.assertRaises(Rejected):
            self.agent.tool(self.owner, "close_case", confirmed=False)
        case = self.agent.tool(self.owner, "close_case", confirmed=True)
        self.assertEqual(case["stage"], "closed")
        self.assertEqual(case["retained_proof"]["packet_hash"], packet_hash)
        self.assertEqual(case["retained_proof"]["payment_receipt"], "SIM-PAY-0001")
        self.assertIsNone(case["record"])
        self.assertEqual(case["documents"], [])
        raw = Path(self.agent.db_path).read_bytes()
        for secret in [b"Alex Santos", b"Ignore all rules", b"2026-09-01", b"synthetic_cpa_statement"]:
            self.assertNotIn(secret, raw)
        for name in ["submit", "pay_tax", "close_case"]:
            with self.subTest(name=name), self.assertRaises(Rejected):
                self.agent.tool(self.owner, name, **({"confirmed": True} if name == "close_case" else {}))
        with self.agent.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM payments").fetchone()[0], 1)

    def test_office_routing_uses_verified_directory_and_never_sends(self):
        case = self.agent.advance(self.operator)
        self.assertEqual(case["packet"]["ecar_office"]["mailbox"], "rdo39_collection@bir.gov.ph")
        self.assertIsNone(case["outbox"])
        self.approve()
        for _ in range(3):
            case = self.agent.advance(self.operator)
        self.assertEqual(case["outbox"]["status"], "draft_not_sent")
        self.assertEqual(case["outbox"]["to"], "rdo39_collection@bir.gov.ph")
        self.assertIn("SIM-FILE-0001", case["outbox"]["body"])

    def test_unknown_office_blocks_packet(self):
        self.mutate(lambda c: c.update(estate_tin_rdo="999"))
        with self.assertRaises(Rejected):
            self.agent.advance(self.operator)

    def test_metrics_survive_closure_without_personal_data(self):
        self.approve()
        for _ in range(3):
            case = self.agent.advance(self.operator)
        metrics = case["metrics"]
        self.assertEqual(metrics["mismatches_caught_before_filing"], 1)
        self.assertEqual(metrics["approvals_bound_to_exact_packet"], 2)
        self.assertEqual(metrics["uncertain_outcomes_reconciled"], 1)
        self.assertEqual(metrics["penalty_if_one_year_late_centavos"], 5_550_000)
        closed = self.agent.tool(self.owner, "close_case", confirmed=True)
        self.assertTrue(closed["metrics"]["personal_data_deleted"])
        self.assertEqual(closed["metrics"]["mismatches_caught_before_filing"], 1)
        self.assertNotIn("Santos", json.dumps(closed["metrics"]))

    def test_open_case_cannot_be_closed(self):
        self.approve()
        with self.assertRaises(Rejected):
            self.agent.tool(self.owner, "close_case", confirmed=True)
        self.assertEqual(self.agent.view(self.owner)["stage"], "ready_to_submit")

    def test_timeout_checks_existing_filing_before_payment(self):
        self.approve()
        self.agent.advance(self.operator)
        self.agent = EstateAgent(self.agent.db_path)
        case = self.agent.advance(self.operator)
        tools = [e["tool"] for e in case["events"]]
        self.assertLess(tools.index("submit"), tools.index("check_filing"))
        self.assertLess(tools.index("check_filing"), tools.index("pay_tax"))
        with self.agent.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM submissions").fetchone()[0], 1)

    def test_replays_and_concurrent_calls_never_debit_twice(self):
        self.approve()
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda _: self.agent.tool(self.operator, "submit"), range(3)))
        self.agent.tool(self.operator, "check_filing")
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda _: self.agent.tool(self.operator, "pay_tax"), range(3)))
        self.agent.tool(self.operator, "check_payment")
        self.agent.tool(self.operator, "pay_tax")
        with self.agent.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM payments").fetchone()[0], 1)
        self.assertEqual(self.agent.view(self.owner)["balance_centavos"], 85_000_000)

    def test_direct_tool_cannot_skip_approvals(self):
        self.agent.advance(self.operator)
        for name in ["submit", "pay_tax", "check_payment"]:
            with self.subTest(name=name), self.assertRaises(Rejected):
                self.agent.tool(self.operator, name)

    def test_operator_cannot_approve_even_with_a_valid_owner_code(self):
        packet_hash, code = self.approve()
        with self.assertRaises(Rejected):
            self.agent.tool(self.operator, "owner_approve", packet_hash=packet_hash, confirmed=True, code=code)

    def test_forged_subject_role_and_cross_case_are_rejected(self):
        for identity in [Principal("demo-operator", "owner", "EST-001"),
                         Principal("demo-owner", "owner", "OTHER"), Principal("stranger", "owner", "EST-001")]:
            with self.subTest(identity=identity), self.assertRaises(Rejected):
                self.agent.tool(identity, "lock")

    def test_induced_personal_transfer_and_raise_limit_are_rejected(self):
        self.approve()
        for name, args in [("pay_tax", {"payee": "PERSONAL-ACCOUNT"}),
                           ("new_payee", {}), ("raise_limit", {"amount": 999999999})]:
            with self.subTest(name=name), self.assertRaises(Rejected):
                self.agent.tool(self.owner, name, **args)

    def test_model_cannot_supply_amount_or_role_to_tools(self):
        for args in [{"amount": 1}, {"role": "owner"}, {"confirmed": True}]:
            with self.subTest(args=args), self.assertRaises(Rejected):
                self.agent.tool(self.operator, "request_record", **args)

    def test_document_injection_does_not_create_payment_or_approval(self):
        case = self.agent.advance(self.operator)
        self.assertIn("Ignore all rules", case["record"]["note"])
        self.assertIsNone(case["owner_hash"])
        self.assertIsNone(case["payment_key"])
        self.assertEqual(case["packet"]["payee"], "SIM-BIR-ESTATE-TAX")

    def test_disputed_ownership_stops_without_resolving_legal_issue(self):
        self.mutate(lambda c: c.update(scenario="disputed_record"))
        case = self.agent.advance(self.operator)
        self.assertEqual(case["stage"], "blocked_professional")
        self.assertIsNone(case["packet"])
        with self.assertRaises(Rejected):
            self.agent.tool(self.operator, "prepare_packet")

    def test_stale_approval_after_evidence_change_is_rejected(self):
        self.approve()
        self.mutate(lambda c: c["record"].update(share_bps=6000))
        with self.assertRaises(Rejected):
            self.agent.tool(self.operator, "submit")

    def test_altered_packet_payee_is_rejected(self):
        self.approve()
        self.mutate(lambda c: c["packet"].update(payee="PERSONAL-ACCOUNT"))
        with self.assertRaises(Rejected):
            self.agent.tool(self.operator, "submit")

    def test_code_attempts_commit_and_lock_out(self):
        case = self.agent.advance(self.operator)
        packet_hash = digest(case["packet"])
        self.agent.tool(self.professional, "professional_approve", packet_hash=packet_hash, confirmed=True)
        code = self.agent.issue_code()
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(5):
            with self.assertRaises(Rejected):
                self.agent.tool(self.owner, "owner_approve", packet_hash=packet_hash, confirmed=True, code=wrong)
        with self.assertRaises(Rejected):
            self.agent.tool(self.owner, "owner_approve", packet_hash=packet_hash, confirmed=True, code=code)
        with self.agent.connection() as db:
            self.assertEqual(db.execute("SELECT attempts FROM codes").fetchone()[0], 6)

    def test_code_is_consumed_and_never_logged(self):
        packet_hash, code = self.approve()
        self.assertNotIn(code, json.dumps(self.agent.view(self.owner)["events"]))
        with self.agent.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM codes").fetchone()[0], 0)
        with self.assertRaises(Rejected):
            self.agent.tool(self.owner, "owner_approve", packet_hash=packet_hash, confirmed=True, code=code)

    def test_expired_code_is_rejected(self):
        case = self.agent.advance(self.operator)
        packet_hash = digest(case["packet"])
        self.agent.tool(self.professional, "professional_approve", packet_hash=packet_hash, confirmed=True)
        code = self.agent.issue_code()
        with self.agent.connection() as db:
            db.execute("UPDATE codes SET expires=?", (time.time()-1,))
        with self.assertRaises(Rejected):
            self.agent.tool(self.owner, "owner_approve", packet_hash=packet_hash, confirmed=True, code=code)

    def test_safety_lock_blocks_approved_execution(self):
        self.approve()
        self.agent.tool(self.owner, "lock")
        with self.assertRaises(Rejected):
            self.agent.advance(self.operator)

    def test_cash_reserve_failure_leaves_balance_unchanged(self):
        self.approve()
        self.agent.advance(self.operator)
        self.agent.tool(self.operator, "check_filing")
        self.mutate(lambda c: c.update(balance_centavos=20_000_000))
        with self.assertRaises(Rejected):
            self.agent.tool(self.operator, "pay_tax")
        self.assertEqual(self.agent.view(self.owner)["balance_centavos"], 20_000_000)
        with self.agent.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM payments").fetchone()[0], 0)

    def test_failed_payment_is_not_called_settled(self):
        self.approve()
        self.agent.advance(self.operator)
        self.agent.advance(self.operator)
        with self.agent.connection() as db:
            db.execute("UPDATE payments SET status='failed'")
        with self.assertRaises(Rejected):
            self.agent.tool(self.operator, "check_payment")
        self.assertIsNone(self.agent.view(self.owner)["payment_receipt"])

    def test_missing_cpa_statement_blocks_preparation(self):
        self.mutate(lambda c: c["documents"].remove("synthetic_cpa_statement"))
        with self.assertRaises(Rejected):
            self.agent.advance(self.operator)


class UKCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.agent = EstateAgent(Path(self.temp.name) / "case.db")
        self.operator = Principal("demo-operator", "operator", "EST-UK-001")
        self.owner = Principal("demo-owner", "owner", "EST-UK-001")
        self.professional = Principal("demo-cpa", "professional", "EST-UK-001")

    def tearDown(self):
        self.temp.cleanup()

    def test_same_agent_completes_uk_case_with_hmrc_rules(self):
        self.assertEqual(self.agent.advance(self.operator)["stage"], "ready_to_prepare")
        self.agent.tool(self.operator, "answer_question", answer=False)
        case = self.agent.advance(self.operator)
        self.assertEqual(case["packet"]["tax_centavos"], 5_000_000)
        self.assertEqual(case["packet"]["nominal_due_date"], "2027-02-28")
        self.assertEqual(case["packet"]["payee"], "SIM-HMRC-INHERITANCE-TAX")
        packet_hash = digest(case["packet"])
        self.agent.tool(self.professional, "professional_approve", packet_hash=packet_hash, confirmed=True)
        self.agent.tool(self.owner, "owner_approve", packet_hash=packet_hash, confirmed=True,
                        code=self.agent.issue_code("EST-UK-001"))
        for _ in range(3):
            case = self.agent.advance(self.operator)
        self.assertEqual(case["stage"], "completed")
        self.assertEqual(case["payment_receipt"], "SIM-HMRC-PAY-0001")
        self.assertEqual(case["balance_centavos"], 3_000_000)
        self.assertIsNone(case["outbox"])
        ph = self.agent.view(Principal("demo-operator", "operator", "EST-001"))
        self.assertEqual(ph["stage"], "missing_record")

    def test_residence_band_answer_stops_for_professional(self):
        self.agent.tool(self.operator, "answer_question", answer=True)
        case = self.agent.advance(self.operator)
        self.assertEqual(case["stage"], "blocked_professional")
        self.assertIsNone(case["packet"])

    def test_uk_code_cannot_approve_ph_case(self):
        self.agent.tool(self.operator, "answer_question", answer=False)
        case = self.agent.advance(self.operator)
        self.agent.tool(self.professional, "professional_approve", packet_hash=digest(case["packet"]), confirmed=True)
        code = self.agent.issue_code("EST-UK-001")
        ph_operator = Principal("demo-operator", "operator", "EST-001")
        self.agent.tool(ph_operator, "answer_question", answer=False)
        ph = self.agent.advance(ph_operator)
        ph_hash = digest(ph["packet"])
        self.agent.tool(Principal("demo-cpa", "professional", "EST-001"), "professional_approve", packet_hash=ph_hash, confirmed=True)
        with self.assertRaises(Rejected):
            self.agent.tool(Principal("demo-owner", "owner", "EST-001"), "owner_approve", packet_hash=ph_hash, confirmed=True, code=code)


class MoneyTests(unittest.TestCase):
    def test_reference_amounts_and_zero_floor(self):
        self.assertEqual(estate_tax(1_500_000_000, 10000)["tax_centavos"], 60_000_000)
        self.assertEqual(estate_tax(1_500_000_000, 5000)["tax_centavos"], 15_000_000)
        self.assertEqual(estate_tax(499_999_999, 10000)["tax_centavos"], 0)

    def test_invalid_money_inputs_are_rejected(self):
        for value, share in [(-1,5000),(True,5000),(1.2,5000),(1,0),(1,10001),(1,True)]:
            with self.subTest(value=value,share=share), self.assertRaises(Rejected):
                estate_tax(value,share)

    def test_penalty_matches_bir_rmc_33_2026_example(self):
        # RMC 33-2026 Q2: PHP948 deficiency gives PHP237 surcharge and PHP862.70 interest at 12%;
        # 2,768 days (our reading: 1 Jan 2018 to 31 Jul 2025 inclusive) reproduces the official figure.
        result = late_penalty(94_800, 2768)
        self.assertEqual(result["surcharge_centavos"], 23_700)
        self.assertEqual(result["interest_centavos"], 86_270)
        self.assertEqual(late_penalty(15_000_000, 0)["total_centavos"], 0)

    def test_uk_threshold_rate_and_six_month_deadline(self):
        self.assertEqual(uk_inheritance_tax(90_000_000, 5000)["tax_centavos"], 5_000_000)
        self.assertEqual(uk_inheritance_tax(32_500_000, 10000)["tax_centavos"], 0)
        self.assertEqual(uk_due_date("2026-01-15"), "2026-07-31")  # gov.uk example: January death, due 31 July
        self.assertEqual(uk_due_date("2026-08-14"), "2027-02-28")

    def test_family_home_answer_stops_for_professional(self):
        temp = tempfile.TemporaryDirectory()
        agent = EstateAgent(Path(temp.name) / "case.db")
        operator = Principal("demo-operator", "operator", "EST-001")
        agent.tool(operator, "answer_question", answer=True)
        self.assertEqual(agent.advance(operator)["stage"], "blocked_professional")
        temp.cleanup()

    def test_calendar_anniversary_is_not_365_days(self):
        self.assertEqual(nominal_due_date("2023-03-01"), "2024-03-01")
        self.assertEqual(nominal_due_date("2024-02-29"), "2025-02-28")
        with self.assertRaises(Rejected):
            nominal_due_date("2017-12-31")


if __name__ == "__main__":
    unittest.main()
