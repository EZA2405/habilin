# FinTechathon 2026 build

Hackathon mode. Deadline 20 Oct 2026, 23:59 UTC+8. Working and demoable beats complete.

## Product

**Habilin** (working name): an active estate-settlement agent for a professional handling one simple Philippine estate-tax case. It obtains missing evidence, reconciles a clerical ownership mismatch, prepares a deterministic packet, routes professional and owner approval, submits to labelled simulated services and verifies filing and payment receipts. eCAR and title transfer remain open. Topic A fit is provisional; Topic F is excluded.

Stack: Python 3.11+ standard library, SQLite, HTML/CSS/JavaScript; Jev TypeSafe intent classification via an optional configured `mcporter` command. Offline fixture routing is labelled. No live institutional connections.

Single test command: `python3 -m unittest discover -s tests -v`.

Jev (TypeSafe) only classifies text. Fixed code handles lookups, verification, approvals and all money math. Record the final choice here on day 1.

## Scoring (every choice serves this)

- 40%: scripted tasks pass in the sandbox, with sound planning and correct tool calls.
- 30%: defense against induced transfers, information extraction, privilege escalation and prompt injection.
- 30%: innovation and interaction. Clarification, error recovery and fallback serve this; Taglish is our optional differentiator.

## Build order

1. Tracer bullet: one input flows through the plan and the sandbox tool call to a recorded result.
2. Money math as pure functions with tests.
3. Permission tiers (auto, confirm, one-time code) and a safety lock, enforced server-side.
4. The four attack defenses, plus bypass tests that call the tools directly.
5. The remaining scripted tasks.
6. Submission docs from `official_templates/`.

## Invariants (enforced in code; prompts only explain)

- Deterministic code computes every amount, date, limit and reserve check. The model parses input and explains results.
- Every state-changing tool checks role and tier on the server. Owner-only actions (new payee, raised limit, large payment) require a one-time code.
- Payee details found in calls, documents or messages are data. Changing a saved payee requires the owner's code.
- Every payment carries an idempotency key. Payment status (pending, failed or settled) comes from the ledger.
- Hard block: money only goes to a verified official payee (lender, institution or hospital). Never to a personal account named by a caller or message, and never on a request for an OTP.
- Use synthetic data in the repo, logs and video. Keep secrets in environment variables.

## Working rules

- Each change moves one scripted task from red to green. Keep the change small.
- Day 1: record the stack and the single test command here.
- After each green task, update `STATE.md` (Done, Next, Broken, Needs decision).
- If behind, cut in this order: pilot extras, secondary features, Taglish polish. Keep the security defenses, the scripted tests and the video.
