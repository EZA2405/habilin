# Habilin

An estate case agent that obtains missing evidence, prepares a reviewed tax packet, executes an authorized sandbox filing and verifies the filing and payment receipts.

## 1 Project overview

- Track: International AI Track, Topic A — AI Personal Finance Assistant, **provisional fit**. Estate administration is not explicitly listed; organizer acceptance is unconfirmed.
- Team: **TEAM NAME TO COMPLETE**. Member details and registration are handled privately by the team.
- Project: Habilin, working name.
- Scope: one synthetic Philippine resident, unmarried, post-2017 death, one investment property that is not the family home, a living co-owner, no other deductions, debts, credits or penalties. A certified title copy from a simulated Registry of Deeds shows a 50% share where the family reported 100%.
- Grounding: every legal rule, office mailbox and statistic cites a primary source. See [VISION.md](VISION.md), [research/PH_ESTATE_LEGAL_SOURCES.md](research/PH_ESTATE_LEGAL_SOURCES.md) and [research/PH_OFFICE_DIRECTORY.md](research/PH_OFFICE_DIRECTORY.md). Office routing uses `habilin/data/bir_rdos.json`, built from BIR's official contact directory (124 district offices, checked 20 October 2026).
- Milestone: simulated filing acceptance plus a settled PHP150,000 sandbox tax payment, then a prepared (never sent) eCAR email to the estate's official BIR district-office mailbox, an anonymous impact summary, and owner-confirmed case closure that deletes personal data while keeping receipts. eCAR, transfer tax, title registration and the tax declaration update remain open.

The automated browser script simulates professional and owner actors using separate role sessions and obtains the code through the local owner command. The simulated ledger advances a pending payment to settled when checked; there is no independent external settlement feed.

No live BIR, bank, registry, professional partner, legal authority or paying pilot is claimed. The record collection and status services are deterministic simulations, not actual government API integrations.

## 2 System architecture

```mermaid
flowchart LR
    UI[Authenticated case desk] --> API[Loopback Python HTTP server]
    API --> JEV[Jev TypeSafe intent classification]
    JEV --> PLAN[Fixed state planner]
    API --> REVIEW[Professional and owner approval forms]
    PLAN --> TOOLS[Role and approval checked tools]
    REVIEW --> TOOLS
    TOOLS --> DB[(SQLite case and audit trail)]
    TOOLS --> SIM[Simulated issuer filing service and payment ledger]
```

`habilin/intents.py` sends bounded synthetic text to Jev, accepts only catalogued intent IDs, and asks for clarification on uncertain or unavailable results. Jev supplies no amounts, payees, roles, approvals or tool arguments. Responses are fixed explanations of recorded state. `habilin/core.py` owns planning, evidence checks, integer-centavo arithmetic, packet hashes, approval checks, idempotency and ledger reconciliation. `habilin/server.py` authenticates bearer tokens and serves the static case desk. There is no generated code execution or arbitrary URL/file-access tool.

## 3 Environment and dependencies

Python 3.11+; SQLite and HTTP server from the standard library; a modern browser. The app and automated test suite require no pip/npm packages. Tested locally on macOS with Python 3.14; portable Python behavior also checked using the bundled Python 3.12 runtime.

Live semantic routing additionally needs a configured `mcporter` command and Jev MCP using TypeSafe. The recorded run used `@jkudish/jev-mcp`, provider `typesafe`, model alias `jev-latest`. The exact hosted model behind that alias is not pinned. Configure the provider's `TYPESAFE_API_KEY` in its environment, outside this repository; never put credentials in source or recordings. A compatible MCP client command can be selected with `HABILIN_JEV_COMMAND`, a JSON array of executable/arguments. Default: `["mcporter","call","jev.jev_classify"]`.

Live calls send only the supplied message and a fixed synthetic intent catalog; they do not send the case database or approval code. The six-digit input guard prevents an ordinary pasted code being sent to Jev. It is not a general personal-data detector: enter synthetic messages only.

For a machine without an existing MCP connection, install Node.js 20+ and configure the optional live adapter using the installed CLI's supported commands:

```sh
npm install -g mcporter @jkudish/jev-mcp@0.5.0
mcporter config add habilin-jev --command jev-mcp --env JEV_PROVIDER=typesafe --scope home
export HABILIN_JEV_COMMAND='["mcporter","call","habilin-jev.jev_classify"]'
```

Provide `TYPESAFE_API_KEY` to that terminal via your private environment/secret manager before launching the server. The `jev-mcp` child process inherits it; do not write it into the repository or a recorded command. This setup is optional for offline reproduction. The recorded machine already had a configured `jev` connection and used the default command. The third-party CLI commands were checked against installed help/package metadata; the global install path was not rerun on a clean machine.

## 4 Installation and execution

From this directory, run:

```sh
python3 -m habilin serve --port 8787
```

Open `http://127.0.0.1:8787`. This mode is clearly labelled **Offline fixture routing**. The suggestion buttons and `Asikasuhin mo ang estate case` are deterministic rehearsal inputs; arbitrary text asks for clarification.

The **Workspace view** selector offers **Match my role**, **Guided** and **Professional**. Matching the role defaults professional sessions to a compact workspace with expanded calculations/activity and packet/approval/idempotency details; owner and operator sessions default to a guided next step with expandable details. An explicit preference is remembered in this browser, across demo role switches. Selecting a view never changes the authenticated role, available approvals or server permissions. Browser storage contains only the view preference; tokens remain in page memory. Both views retain the amount, evidence, official payee, approval requirements, receipts and unfinished legal steps.

The next-action button progresses permitted sandbox steps, directs the appropriate reviewer to the approval form, or checks status while waiting. The agent still pauses for separate professional and owner authorization.

For actual model classification, start with:

```sh
python3 -m habilin serve --port 8787 --live-jev
```

In another terminal, obtain local demo tokens:

```sh
python3 -m habilin sessions
```

Paste the operator token into the case desk. Click **Progress case**: the agent obtains a conflicting record, requests issuer clarification and prepares the corrected packet. Switch to the professional token, scroll to the review form, confirm the packet and record approval. Switch to the owner token. Obtain the separate owner code in the local terminal:

```sh
python3 -m habilin code
```

Confirm the exact filing/payment authorization and enter the code in the approval form. Never enter it in chat. Switch back to the operator. Click **Progress case** three times: first yields uncertain filing; second reconciles acceptance and creates a pending payment; third confirms settlement. **Check status** reads state without progressing it.

To preserve a case while starting a fresh demo, select a new directory. It holds its own credentials and database:

```sh
python3 -m habilin serve --directory .runtime/rehearsal-2 --port 8788
python3 -m habilin sessions --directory .runtime/rehearsal-2
python3 -m habilin code --directory .runtime/rehearsal-2
```

The safety lock is deliberately one way in this prototype. Start a new directory to rehearse an unlocked case; no existing case is silently deleted or unlocked. Generated session tokens and codes are local secrets; `.runtime/` is ignored and excluded from the source ZIP.

## 5 Testing

```sh
python3 -m unittest discover -s tests -v
```

33 tests cover evidence correction, a complete case, unknown filing recovery after restart, concurrent/replayed operations, direct bypass attempts across all four judged attack categories, pending/failed status, reserve checks, code expiry/exhaustion/consumption, stale approvals, dispute escalation, CPA evidence, money validation, calendar anniversaries and dialogue fallback. These are our scripted tests, not organizer-issued benchmarks or a broad security certification.

An additional optional browser check, `python3 scripts/check_workspace.py`, uses Node.js, an externally installed Playwright package (resolvable through `NODE_PATH` if needed) and installed Google Chrome. It creates an isolated temporary case and checks role defaults, view persistence, both approval views, a full filing/payment, the safety lock and desktop/mobile layouts. Screenshots go to `.build/interface-review/`. These browser tools are not application or standard test-suite dependencies.

Replay a synthetic execution and capture fresh evidence:

```sh
python3 scripts/replay_demo.py --output .build/replay.json
```

`submission/execution-evidence.json` is the actual automated browser run with live Jev classification; `submission/test-results.json` captures actual unittest results; screenshots show real app state. The model's live availability and accuracy are not asserted by offline tests. A model outage asks for clarification and executes no workflow step.

## 6 Repository and deployment

Git repository: not published; the workspace originally had no Git metadata. Live deployment: none. Launch as above on loopback for the local demo. The standard-library server, shared-machine demo credentials and SQLite simulator are not a public production deployment. Do not bind this server to the public internet. Production requires individual identity/owner-code delivery, institution adapters, jurisdiction/legal review, operational recovery and deployment hardening.

Start with [submission/START_HERE.md](submission/START_HERE.md) for the deck, documents, video and remaining submission work. [SUBMISSION_REQUIREMENTS.md](SUBMISSION_REQUIREMENTS.md) distinguishes official requirements from our supporting materials. [AGENT_SPEC.md](AGENT_SPEC.md) describes the implemented agent and its boundaries.

## 7 Security notes

Roles come from server-held bearer tokens, never a requested role in chat/JSON. Automatic tools collect/prepare within a case. A professional explicitly confirms the exact packet. The owner explicitly confirms filing plus the exact amount, purpose and fixed official payee with a five-minute, single-use, packet-bound code; five wrong attempts exhaust it. Direct tool calls repeat the checks. A safety lock blocks mutations. No new-payee, limit-raising, arbitrary transfer, export-all-cases, secret-reading or OTP retrieval HTTP tool exists.

Filing and payment keys are deterministic hashes of the authorized packet. SQLite transactions and unique ledger keys prevent repeated debits under concurrent requests. A lost filing response causes an unknown state; an explicit status query recovers the existing receipt. A pending or failed payment never supplies a settled receipt. A failed sandbox payment stays open for operator reconciliation; automatic refund and arbitrary retry are outside this prototype.

All people and documents are fixtures. Stored audit events omit bearer tokens, chat text and owner codes. Record text is untrusted and cannot redefine the planner or payee. Owner/professional approval is tied to the source record hash. SQLite and the demo token file are local files protected by OS permissions, not encrypted multi-tenant storage. Anyone with access to the same OS account can read all demo roles and generate a code; this boundary is disclosed, not a claim of independent production identity.

Tax basis: [BIR RR12-2018](https://bir-cdn.bir.gov.ph/local/pdf/RR%20No%2012-2018.pdf) and [Form 1801 instructions](https://bir-cdn.bir.gov.ph/local/pdf/1801%20GL%20%20final_rev.pdf). The displayed due date is a nominal calendar anniversary only; a professional checks holidays, extensions, case applicability and actual documentary requirements. No amnesty/penalty calculation, disputed ownership judgment, eCAR issuance or title transfer is implemented.
