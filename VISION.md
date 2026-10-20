# Habilin vision

Draft, 20 October 2026. Rule for everything below: every claim about the problem, the law or our impact cites a real source. Anything not yet sourced is marked **TO VERIFY**. Research inputs: `research/PH_ESTATE_LEGAL_SOURCES.md`, `research/PH_OFFICE_DIRECTORY.md`, `research/GLOBAL_ESTATE_HEADLINES.md` plus `research/ph_offices.json` (all 124 BIR district offices with official mailboxes), plus the verified files listed at the end.

## One line

Habilin is an AI agent that does the work of settling an estate, not just advising on it.

## The problem

When someone dies, their property is frozen until a chain of paperwork clears. That chain runs across many offices, documents and deadlines. Families stall, and assets sit idle for years.

Verified so far:
- Philippines: 133,860 beneficiaries used the estate-tax amnesty, paying PHP7.41B (through March 2023). [PIA](https://mirror.pia.gov.ph/news/2023/09/16/bir-tagum-wages-info-drive-on-new-estate-tax-amnesty-program)
- Philippines: DOF backed extending the amnesty to 2028, citing idle assets. The last amnesty closed June 2025; the extension is a bill, not law. [DOF](https://www.dof.gov.ph/go-greenlights-extension-of-estate-tax-amnesty-to-reducefinancial-burden-on-filipino-families-settling-obligations/)
- Philippines: 566,709 registered deaths, January to November 2025 (potential estate events, not customers). [Tribune / PSA](https://tribune.net.ph/2026/05/26/births-marriages-deaths-decline-in-2025-psa)
- Malaysia: 46,707 unresolved small-estate cases at end of 2025; causes include incomplete ownership documents and multi-agency document collection. [NRES](https://www.nres.gov.my/parlimen/Lists/papar-Jawapan-Parlimen.aspx?ID=++++2986)
- Japan: unregistered inheritance is about two-thirds of the causes of owner-unknown land. [MOJ](https://www.moj.go.jp/MINJI/minji05_00599.html)
- India: unclaimed bank deposits rose 26% to Rs 78,213 crore; RBI says part belongs to deceased depositors whose heirs have not claimed (share not stated). Details and sources: `research/GLOBAL_ESTATE_HEADLINES.md`.
- Malaysia: RM90 billion "estimated" frozen inherited assets is an unaudited parliamentary figure; label it as such if used.
- United States: the regulator's locator has matched about USD16.99B in life policies and annuities families did not know about. [NAIC](https://content.naic.org/article/naic-life-insurance-policy-locator-tool-helps-match-consumers-more-16-billion-lost-and-unclaimed)

## Who uses it

A lawyer, CPA or estate administrator handling the case. The family's authorized representative (the owner) approves anything involving money.

## What it does: six actions

1. **Gather:** requests missing documents from the issuing office.
2. **Reconcile:** finds where documents disagree (ownership share, names, title versus tax declaration) and routes each to the correct legal fix. It never decides a family dispute.
3. **Prepare:** builds the filing. Fixed code computes every amount from the law (NIRC sec. 84 and 86 as amended by RA 10963; RR 12-2018).
4. **Approve:** routes the filing to the professional, then to the owner, bound to the exact amount and official payee.
5. **Submit and pay:** files once and pays only the official office. Recovers from lost replies without double filing or double charging.
6. **Verify and close:** confirms receipts before calling a step done. On closure, deletes personal data and keeps only receipts and approval fingerprints.

## Principles

- **Grounded:** legal rules, office contacts and statistics come from a fixed, sourced reference, not from the model's memory or live searching.
- **Humans approve, code computes:** the model understands requests; deterministic code does every amount, date and permission check.
- **Private by design:** holds personal documents only while the case is open, then deletes them at closure.
- **Proof, not assumptions:** a step is done only when an official receipt confirms it.

## Today versus next

Today (working, tested, simulated offices, synthetic people): one Philippine estate case from missing ownership record to a verified estate-tax filing and payment, then closure with data deletion.

Next, in order:
1. The rest of the Philippine chain: eCAR, transfer tax, Registry of Deeds title transfer, tax declaration update.
2. Real office channels: email to the correct BIR district office from the sourced directory; then official portals (BIR e-filing and e-payment, PSA e-Certificate, LRA online title copies, e-notarization).
3. Many cases at once for one firm; estates with several properties or several generations.
4. Long-term intelligence from anonymous process data only: which office takes how long, which documents are usually missing, where cases stall, plus official zonal values and rule changes.
5. Other countries through their own official rails.

## How we measure helping people

Per case (recorded automatically; no personal data needed):
- Days from case start to tax filed, to tax paid, to eCAR, to new title.
- Mismatches caught before filing (each one avoids a rejected filing or a wrong tax amount).
- Documents obtained by the agent versus by the family.
- Late-filing penalties avoided: 25% surcharge plus 12% a year interest (NIRC sec. 248 and 249; BIR RMC 33-2026 worked example). Source: `research/PH_ESTATE_LEGAL_SOURCES.md`.
- Professional hours per case, and rework (filings returned).
- Personal data deleted at closure: yes or no, for every case.

Across cases: share of cases reaching each milestone, and the median time compared with a published or practitioner-reported baseline (baseline TO VERIFY; no Philippine median is sourced yet).

Today these are measured only on our synthetic demo. Real impact numbers require a pilot with a practitioner, with consent.

## What it is not

Not a will-writing chatbot, a checklist app, or a judge of family disputes. It does not issue government certificates or replace a professional's sign-off.

## Verified source files

`ESTATE_PH_RESEARCH.md`, `HABILIN_PH_LEGAL_EVIDENCE.md`, `ESTATE_INTERNATIONAL_RESEARCH.md`, `research/ESTATE_SEA_QUANTIFIED_RESEARCH.md`, `ACTIONABILITY_RESEARCH.md`.
