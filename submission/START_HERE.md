# Habilin submission package

Habilin is a working local estate-case agent and a draft International AI Track submission. **Team identity, eligibility, registration and final topic acceptance still need your completion. Nothing has been registered, emailed or submitted by the assistant.**

The official working cutoff is **20 October 2026, 23:59 Manila time**. Registration and submission are due the same day. Do not rely on tomorrow for required administrative fields. Sources and exact distinctions: [submission requirements](../SUBMISSION_REQUIREMENTS.md), [IEEE Singapore](https://www.ieee-cis-singapore.org/2026-fintechathon), [organizer rules](https://fintechathon.g-ican.com/#/rule).

## Required materials

| Material | File | What remains |
| --- | --- | --- |
| Registration workbook | Registration-TO-FILL.xlsx | Fill member rows privately; it is an unchanged official blank template |
| English technical document | Habilin-Technical-Document.docx | Team Caelus, Topic B |
| Presentation up to 10 minutes | Habilin-Presentation.pptx and Habilin-Presentation.pdf | 10 slides, about 8 minutes; speaker notes in Habilin-Presentation-Speaker-Notes.md |
| Demo video up to 5 minutes | InternationalAI-Habilin-DemoVideo.mp4 | 1 min 35 s, 1920×1080, burned-in English captions, AI voice narration: real news headlines from five countries, the Philippine problem, then the actual app recorded from a fresh server (clips sped up to match narration), close |

The video guide is supporting production guidance and does not replace the MP4. The public rules do not establish an attachment-size limit, fixed slide count, distinct submission subject, mandatory ZIP name or a mandatory model/provider; follow any additional instructions in your organizer acknowledgment. Topic B, AI Wealth Assistant, is our provisional fit: Habilin protects and transfers a family's inherited wealth. Estate administration is not expressly listed and acceptance is unconfirmed. Topic F is excluded.

## Useful optional supporting materials

- Habilin-Source.zip — app, tests, replay script and completed README; no runtime credentials or private records.
- Habilin-Security-Self-Assessment.docx — permissions, four attack categories, failure recovery and known risks.
- Habilin-Execution-Evidence.docx — actual execution, receipts, links and reproduction.
- execution-evidence.json and test-results.json — actual captured live browser and unittest results.
- screenshots/ — actual app states, including corrected evidence, unknown filing, pending payment and final milestone.
- Habilin-DemoVideo.srt and Habilin-Demo-Script.md — English captions and narration.
- Habilin-Presentation-Speaker-Notes.md — slide-by-slide talk plan for the 10-slide deck (hook, global problem, Philippine 9-step chain, six actions, product, sourced math and routing, trust, impact, scope and roadmap, ask), with primary sources also in slide notes.
- Habilin-Idea-Brief.md — concise idea description for an email or registration narrative.

## Finish and send privately

1. Confirm eligibility: 2–5 full-time students at qualifying institutions outside Mainland China, Hong Kong, Macao and Taiwan; at least 60% non-Chinese nationals, rounded upward; each person belongs to only one team. No eligibility has been established for this team.
2. Complete the workbook in English. In Team Information, rows 3–7 use B name, C nationality, D university, E major, F study year, G email, H phone and I role. Row 3 is the leader. There is no workbook cell for team name, lead country or topic; include those in the email/metadata.
3. Keep identity numbers, enrolment/student-status proofs and all personal documents private. The live rules and workbook defer some proof mechanics to organizer instructions; include them only through the verified private channel when requested.
4. Fill the real team name in all four DOCX files, README/project overview and deck cover. Select one topic consistently after resolving the fit. Do not replace it with a false claim of organizer approval.
5. Use REGISTRATION-EMAIL-DRAFT.txt and SUBMISSION-EMAIL-DRAFT.txt as drafts. Registration goes to fintechathon@ican-x.com with the published subject format. Check the attachment list and organizer reply. Send required artifacts before the cutoff; do not assume that an unsent draft or a prepared folder is registration.
6. Watch the MP4, open the PPTX/DOCX/XLSX in your chosen apps and rehearse once. The deck and documents have been rendered and inspected locally; native PowerPoint/Word/Excel execution has not been checked.
7. Remove unused alternatives and private proofs from any public archive. The prepared source ZIP excludes .runtime, .env, tokens, local database, caches and builds. The complete package archive retains the visibly blank registration form and team placeholders; complete those before sending.

## Run the agent

From the repository or extracted source ZIP: `python3 -m habilin serve --port 8787`. Open `http://127.0.0.1:8787`. Pick a person on the sign-in screen. The default is an explicitly labelled offline rehearsal. Add `--live-jev` with the configured TypeSafe MCP command for actual semantic classification. Full instructions are in [README](../README.md).

As operator progress the case. As professional confirm the exact packet. As owner confirm filing/payment and enter a code from `python3 -m habilin code` in the masked form. As operator progress three times: unknown filing → confirmed filing and pending payment → verified settled payment. Run `python3 -m unittest discover -s tests -v` for the scripted suite and `python3 scripts/replay_demo.py --output .build/replay.json` for an offline tool replay.

## What the demonstration proves

Actual evidence collection through a simulated issuer, a source correction, deterministic PHP150,000 math, separate checked approvals, single-use owner code, idempotency, unknown-status recovery, one sandbox debit and verified receipts. The captured run used live Jev/TypeSafe classification. Forty-nine automated tests passed on Python 3.14 and 3.12. These are our tests and a narrow demonstration, not a security certification or organizer-issued benchmark.

Every institution is simulated and every person/document is synthetic. The product does not issue eCAR, transfer titles, determine disputed ownership, perform a real government filing or make real payments. A professional must validate rules and documents. Shared-machine demo identities, unpinned hosted model alias, no production integrations and no validated commercial advantage remain material limits.

The live browser evidence is an automated Playwright exercise with live Jev classification. Its script simulates professional and owner actors, using separate authenticated sessions and the local owner-code command. The simulated ledger settles when checked; no independent external settlement feed is claimed.

Final checks (20 Oct 2026): the MP4 measures 95.4 seconds at 1920×1080/30fps, H.264 video and AAC audio, peak -3.5 dBFS; frames across the whole video were inspected. The demo segment is an automated browser run of a fresh server (new runtime directory, offline fixture routing, labelled). See video-verification.json.
