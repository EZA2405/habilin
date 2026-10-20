# Habilin security self-assessment

Scope: the local demo in this repository. All institutions are simulated and all people are synthetic. The Word version for the official template is `docs/Habilin-Security-Self-Assessment.docx`.

## Permission model

| Person (role) | Can do | Cannot do |
| --- | --- | --- |
| Case operator | Ask the agent to gather evidence, prepare the packet, file and pay an already-approved packet | Approve anything, change amounts or payees |
| Professional | Approve the exact prepared packet | File, pay, or approve for the owner |
| Family representative (owner) | Authorize filing and payment with a single-use code; lock the case; close it and delete personal data | Send money anywhere except the verified official payee |

Roles come from the server-held session token, never from chat text or request fields. Every state-changing tool re-checks role, case stage and the packet fingerprint on the server.

## Money controls

- Fixed code computes every amount in integer centavos. The model never supplies a number, payee, role or approval.
- Money only goes to the verified official payee, which is sealed inside the approval fingerprint. Any change to amount, payee, evidence or assumptions voids earlier approvals.
- The owner code is six digits, single-use, bound to the packet, expires in five minutes and locks out after failed attempts. It is issued outside the app (`python3 -m habilin code`) and never typed into chat.
- Filing and payment carry idempotency keys. A lost reply is reconciled against the existing submission; replays and concurrent requests never debit twice. Payment status comes from the ledger.
- The owner's safety lock blocks even an approved case.

## The four attack classes

| Attack | Defense | Example tests |
| --- | --- | --- |
| Induced transfer | Only the verified official payee; personal accounts, new payees and raised limits rejected | `test_induced_personal_transfer_and_raise_limit_are_rejected`, `test_altered_packet_payee_is_rejected` |
| Information extraction | Six-digit codes caught before any model call (after Unicode normalization); requests scoped to the session's case; no routes to secrets | `test_otp_never_reaches_model`, `test_secrets_and_other_case_are_not_routes`, `test_unicode_obfuscated_owner_code_never_reaches_external_classifier` |
| Privilege escalation | Role from the session token, checked inside each tool; request bodies cannot claim a role | `test_operator_cannot_approve_even_with_a_valid_owner_code`, `test_request_body_cannot_claim_owner_role` |
| Prompt injection | Documents and chat are data; the model only returns one of seven intent labels; reworded replies that mention codes or money movement fall back to the fixed reply | `test_document_injection_does_not_create_payment_or_approval`, `test_model_cannot_supply_amount_or_role_to_tools`, `test_injected_model_reply_cannot_solicit_owner_code_or_personal_transfer` |

## Testing and red-team

`python3 -m unittest discover -s tests -v` runs 70 tests. `tests/test_adversarial.py` holds 20 attacks written by an independent AI red-team (OpenAI Codex) that tried to trick the agent through the HTTP API and the tool layer. It found two issues, both fixed on 20 October 2026:

1. An owner code split by zero-width or Unicode-dash characters slipped past the code filter and reached the intent classifier. Fixed by normalizing the text and removing invisible and dash characters before the check (`habilin/intents.py`).
2. An optional reworded reply could ask the user for their code or a transfer. Reworded replies that mention codes, PINs, transfers or personal accounts now fall back to the fixed reply (`habilin/narrate.py`).

## Known limits

- Local demo: `/api/demo-session` gives the three role tokens to a page on the loopback host so one screen can play all three people; it rejects foreign `Host` and `Origin` headers. Anyone with access to the same operating-system account can read the demo tokens and generate a code. This is disclosed, not a production identity system.
- SQLite and the token file are protected by file permissions, not encryption. Closing a case deletes personal records with SQLite `secure_delete`, keeping receipts and approval fingerprints.
- No real government, bank or registry is connected. Live model accuracy is not asserted by offline tests; a model outage leads to a clarifying question, never an action.
