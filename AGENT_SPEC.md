# Habilin agent definition

Habilin progresses an authorized estate-tax case to a verified sandbox filing and payment milestone. Its operator is a case handler working with an authorized representative and a reviewing professional. Repeated use by an estate law/accounting practice is a buyer hypothesis, not established demand.

## Inputs and case form

The demo form selects an authenticated role token and operates one existing synthetic case. It does not accept real personal records. Case EST-001 stipulates a resident, unmarried decedent, death on 10 April 2026, PHP15m investment property, no other deductions/credits/debts/penalties, an intake share of 100%, and a source-confirmed share of 50%. Five supporting fixture documents include authority, death evidence, valuation, settlement evidence and CPA statement. The local planner uses the corrected evidence only as a proposal awaiting professional approval.

## Cases and interface

One engine runs two synthetic cases with local rules: EST-001 (Philippine estate tax: BIR, 6% above the PHP5M standard deduction, one calendar year to file) and EST-UK-001 (UK Inheritance Tax: HMRC, 40% above the GBP325,000 threshold, due by the end of the sixth month after death). Jurisdiction rules (tax formula, deadline, late cost, payee, limits, office routing, required document) live in `RULES` in `habilin/core.py`; adding a country means adding a rule set, not changing the agent. The browser selects the case with an `X-Case-Id` header; the server validates it.

The interface puts every action in one "What happens next" card: the next-step button, the clarifying question (Yes/No), and the professional or owner approval form. Details sit in tabs (Tax, Evidence, Offices & next steps, Impact, Technical). A demo link signs in all three roles; "Acting as" tabs switch between them, and each request carries that role's own token.

## Goal and finish condition

Obtain missing ownership evidence, resolve a clerical mismatch through the simulated issuer, prepare the restricted tax packet, request professional and owner approval, submit once, recover from a lost response, make one authorized official-payee sandbox payment, and verify settlement. Finish only when filing and settled ledger receipts match the exact approved packet. Continue to display government review, eCAR and actual title transfer as unfinished work.

## Model contract

Jev TypeSafe classifies text into `unsafe`, `progress`, `status`, `explain`, `correction`, `off_topic` or `unclear`. `habilin/intents.py` contains the exact descriptions and acceptance thresholds: top probability at least 0.85 and margin at least 0.5, with a valid catalog ID and provider response. It is a classifier with a deterministic planner; no free-form model plan or tool-call generation is claimed. The model cannot authorize, compute money, select a destination or edit case facts. Replies describe recorded state using fixed templates. Uncertain or unavailable classification asks for clarification and does not progress the case.

## Tools and authority

| Tool | Role and tier | Result |
| --- | --- | --- |
| request_record | Operator or owner; automatic | Calls the simulated issuer; stores record and ownership conflict |
| resolve_record | Operator or owner; automatic | Obtains issuer correction, or stops for disputed ownership |
| prepare_packet | Operator or owner; automatic | Validates fixture scope/CPA evidence; computes integer-centavo packet |
| professional_approve | Professional; explicit confirmation | Records approval of exact current packet and evidence hash |
| owner_approve | Owner; confirmation plus separate code | Authorizes one filing and the exact amount/purpose/official payee |
| submit | Operator or owner; both bound approvals | Uses one idempotency key; simulated lost response leaves unknown status |
| check_filing | Operator or owner; both bound approvals | Reads simulated filing receipt before a payment can proceed |
| pay_tax | Operator or owner; both bound approvals | Verifies official payee, amount limit and reserve; ledger debit once |
| check_payment | Operator or owner; both bound approvals | Simulated ledger settles, then agent reads the settled result |
| answer_question | Operator or owner; form buttons only | Answers the open clarifying question (PH family home; UK home passing to descendants). Yes stops the case for a professional; No records the assumption. Chat cannot answer it |
| lock | Owner | Blocks further mutations; no chat unlock |
| close_case | Owner; explicit confirmation | Only after verified filing and payment. Deletes personal records, documents and activity text; keeps receipts, approval fingerprints and idempotency keys. Allowed while locked. Irreversible |

The Python Principal object is trusted server context. The public HTTP boundary derives it from a secret bearer credential; clients cannot submit a Principal or role override. Direct internal tests exercise the tool checks, while HTTP tests verify the authentication boundary.

## State and error recovery

`missing_record → ownership_conflict → ready_to_prepare → await_professional → await_owner → ready_to_submit → filing_unknown → filed → payment_pending → completed`.

SQLite persists case, packet, approvals, ledger keys, code hashes and audit events. A disputed issuer response becomes `blocked_professional`. A lock, stale hash, missing CPA evidence, reserve failure, invalid code, unavailable model or failed ledger status preserves unfinished work and returns a concrete reason. Status queries do not treat a timeout as failure. Duplicate calls reuse the existing service/ledger key. No automatic refund, legal adjudication or fabricated receipt is allowed.

## Demonstration dialogue

Operator: “Asikasuhin mo ang estate case.” The agent obtains the missing evidence, resolves the intake mismatch and asks for professional review. Professional and owner complete separate authenticated forms. Operator: “Progress this estate case.” The simulated filing times out. “Check case status” reports uncertainty without retrying. “Progress this estate case” reconciles acceptance and shows payment pending. A final progress request verifies settlement and lists the unfinished legal stages.

“The ownership share is wrong” requests source evidence instead of editing the amount. “Yes” asks what action is intended. A personal-account request is refused; tool boundaries reject the destination even if a classifier were mistaken. The demo includes a malicious instruction embedded in the issuer record; it remains inert data.

## Product limits and differentiation to validate

The implemented domain contract connects evidence, approval scope, action identity and authoritative status. This is a useful workflow hypothesis, not a demonstrated moat over Hermes, OpenClaw or any general agent given equal tools. No comparative benchmark, professional pilot, willingness to pay or fee saving has been measured. Next: have a qualified professional review supported cases, compare equal-input/equal-tool completion against an existing workflow, measure interventions and rework, and validate the first institution integration before accepting real records.

The recorded evidence is an automated browser exercise with live model classification. Its script simulates professional/owner actions and obtains the code from the local owner command. The simulated ledger advances to settled when checked; no independent external confirmation feed is claimed.
