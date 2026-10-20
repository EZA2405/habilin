const ROLES = ["operator", "professional", "owner"];
const PLACES = {
  PH: {country: "Philippine estate tax", currency: "PHP", locale: "en-PH", issuer: "Registry of Deeds", record: "title copy", authority: "BIR",
       valueLabel: "Property value at death (higher of BIR zonal or assessor value)",
       taxFine: "Restricted illustration: resident, unmarried, property is not the family home, co-owner alive, no other deductions or credits. Rule: NIRC sections 84 and 86 as amended by RA 10963; RR 12-2018. *A professional confirms the deadline and any relief.",
       penaltyLabel: "Penalty if filed one year late (25% + 12%/yr)",
       impactFine: "Penalty rule: NIRC sections 248 and 249, checked against BIR RMC 33-2026's worked example. Compromise penalties are excluded.",
       officeFine: "Mailboxes come from BIR's official contact directory (124 district offices, checked 20 Oct 2026). Drafts are never sent by the demo; a person reviews and sends them, and original documents are presented at the office."},
  UK: {country: "UK inheritance tax", currency: "GBP", locale: "en-GB", issuer: "HM Land Registry", record: "title register", authority: "HMRC",
       valueLabel: "Property value at death",
       taxFine: "Restricted illustration: England, unmarried, no lifetime gifts or reliefs, home not passing to children or grandchildren. Rule: gov.uk Inheritance Tax, 40% above the £325,000 threshold, paid by the end of the sixth month after death.",
       penaltyLabel: "Interest if paid one year late (7.75%/yr)",
       impactFine: "HMRC late payment interest: 7.75% from 9 January 2026 (gov.uk interest rates page).",
       officeFine: "Next step per gov.uk: HMRC sends a code after payment, then the executor applies for probate. No mailbox is used for this step."},
};
const TONES = {completed: "good", filed: "good", closed: "good", ready_to_submit: "good", ownership_conflict: "warn", blocked_professional: "warn", filing_unknown: "warn",
               await_professional: "action", await_owner: "action", missing_record: "action", payment_pending: "action"};
const PEOPLE = {operator: ["Maria Reyes", "Case operator · paralegal", "MR", "Hi Maria. Press the blue-outlined button to start: I’ll get the official records and prepare the tax. Ask me anything here."],
  professional: ["Atty. Jose Cruz", "Lawyer / CPA", "JC", "Good day, Atty. Cruz. Your part: check the evidence and the exact amount, then approve. Nothing is filed without you."],
  owner: ["Ana Santos", "Family representative", "AS", "Hi Ana. Nothing is filed or paid until you approve with your one-time code. You can also lock or close the case."]};
let tokens = {};
let role = null;
let caseId = "EST-001";
let current;
let packetHash;
let busy = false;
const $ = (id) => document.getElementById(id);
const place = () => PLACES[current?.jurisdiction || (caseId === "EST-UK-001" ? "UK" : "PH")];
const money = (value) => value == null ? "—" : new Intl.NumberFormat(place().locale, {style: "currency", currency: place().currency, maximumFractionDigits: 0}).format(value / 100);

try { caseId = sessionStorage.getItem("habilin.case") || caseId; role = sessionStorage.getItem("habilin.role"); } catch {}
function remember() { try { sessionStorage.setItem("habilin.case", caseId); sessionStorage.setItem("habilin.role", role); } catch {} }

function stageText() {
  const p = place(), c = current, tax = money(c.packet?.tax_centavos);
  const table = {
    missing_record: ["Get the ownership record", `I’ll request the official ${p.record} from the simulated ${p.issuer}, compare it with what the family reported and resolve any difference.`, "Evidence needed", 0],
    ownership_conflict: ["Resolve the ownership difference", `The ${p.record} disagrees with the intake. I’ll confirm it with the issuer before anything is calculated.`, "Evidence conflict", 0],
    ready_to_prepare: c.question ? ["One question before the tax", c.question.text, "Your answer needed", 0]
      : ["Ready to prepare the tax packet", "The evidence is reconciled. I can now compute the exact amount.", "Ready", 0],
    await_professional: ["Professional review needed", `The official ${p.record} shows a 50% share, not the 100% the family reported. A professional confirms the evidence, assumptions and the exact ${tax}.`, "Review required", 1],
    await_owner: ["The owner decides", `The professional approved. The owner authorizes this filing and the exact ${tax} payment with a one-time code.`, "Owner approval", 2],
    ready_to_submit: ["Approved and ready to file", `Both approvals are bound to this exact packet and the official ${p.authority} payee.`, "Authorized", 3],
    filing_unknown: ["Check the filing before retrying", "The simulated service received the filing but its reply was lost. I’ll check the existing filing instead of sending it twice.", "Outcome unknown", 3],
    filed: ["Filing confirmed", "The filing receipt is verified. Next is the one authorized payment.", "Filed", 4],
    payment_pending: ["Verify the payment", `${tax} was debited once. I’ll confirm settlement in the ledger before calling it paid.`, "Payment pending", 4],
    completed: ["Filing and payment verified", "Receipts confirm both. The remaining legal steps are listed under Offices & next steps.", "Milestone complete", 5],
    blocked_professional: ["A person needs to handle this", c.block_reason || "The issuer reports disputed ownership. The workflow is stopped for professional handling.", "Stopped for review", 0],
    closed: ["Case closed · personal data deleted", "Names, records, documents and messages were deleted. Only receipts and approval fingerprints remain as proof.", "Closed", 5],
  };
  return table[c.stage] || ["Case remains open", "Check the recorded activity.", "In progress", 0];
}

function renderAction() {
  const review = !$("approval").hidden;
  const asking = !$("question").hidden;
  const canProgress = ["operator", "owner"].includes(current.role) && !current.locked;
  const actions = {missing_record: "Get evidence & prepare packet", ownership_conflict: "Resolve & prepare packet", ready_to_prepare: "Prepare tax packet",
                   ready_to_submit: "File the approved packet", filing_unknown: "Check filing & pay", filed: "Make the payment", payment_pending: "Verify payment"};
  const action = canProgress && !asking && actions[current.stage];
  // Who acts next; the main button switches to that person so the demo never stalls.
  const needed = {await_professional: "professional", await_owner: "owner"}[current.stage]
    || (actions[current.stage] && current.role === "professional" ? "operator" : null);
  const handoff = needed && needed !== current.role && !current.locked;
  $("next-action").hidden = (review || asking) && !handoff;
  $("next-action").textContent = handoff ? `Hand off to ${PEOPLE[needed][0]}` : action || "Check case status";
  $("next-action").dataset.action = handoff ? `switch:${needed}` : action ? "progress" : "status";
  $("next-action").disabled = busy;
  const short = {operator: "Maria", professional: "Atty. Cruz", owner: "Ana"};
  $("turn").textContent = current.stage === "closed" ? "" : handoff ? `${short[needed]}’s turn` : (action || review || asking) ? `Your turn, ${short[current.role]}` : "";
  const wait = {await_professional: "Next: a professional reviews the exact amount.", await_owner: "Next: the owner approves with a one-time code."};
  $("action-help").textContent = review ? "" : asking ? "A yes sends the case to a professional."
    : current.locked && current.stage !== "closed" ? "Locked by the owner."
    : wait[current.stage] || "";
}

async function api(path, body) {
  const res = await fetch(path, {method: body ? "POST" : "GET", headers: {"Authorization": `Bearer ${tokens[role]}`, "X-Case-Id": caseId, "Content-Type": "application/json"}, body: body ? JSON.stringify(body) : undefined});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Operation failed.");
  return data;
}
function error(text) { $("error").textContent = text; $("error").hidden = !text; }
function message(text, who, source) {
  const div = document.createElement("div"); div.className = `message ${who}`; div.textContent = text;
  if (source) div.title = source;
  $("conversation").append(div); $("conversation").scrollTop = $("conversation").scrollHeight;
}
function showTab(name) {
  document.querySelectorAll("[data-tab]").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll("[data-panel]").forEach((panel) => { panel.hidden = panel.dataset.panel !== name; });
}

async function refresh() {
  const data = await api("/api/state"); current = data.case; packetHash = data.packet_hash;
  const p = place(), packet = current.packet, m = current.metrics || {};
  document.body.dataset.role = current.role;
  $("portal").hidden = true; $("case-desk").hidden = false; $("role-switch").hidden = false;
  $("who-avatar").textContent = PEOPLE[role][2]; $("who-name").textContent = `${PEOPLE[role][0]} · ${PEOPLE[role][1]}`;
  document.querySelectorAll("[data-role]").forEach((b) => { b.disabled = !tokens[b.dataset.role]; b.classList.toggle("active", b.dataset.role === role); b.setAttribute("aria-selected", b.dataset.role === role); });
  document.querySelectorAll("[data-case]").forEach((b) => b.classList.toggle("active", b.dataset.case === caseId));
  $("crumb-case").textContent = current.id; $("case-eyebrow").textContent = p.country;
  $("case-name").textContent = current.label.replace(" · synthetic", ""); $("model-mode").textContent = data.mode;
  const [title, description, chip, step] = stageText();
  $("stage-title").textContent = title; $("stage-description").textContent = description; $("stage-chip").textContent = chip; $("stage-chip").dataset.tone = TONES[current.stage] || (current.question ? "action" : "");
  document.querySelectorAll("[data-step]").forEach((el, i) => { el.className = i < step ? "done" : i === step ? "current" : ""; el.querySelector("i").textContent = i < step ? "✓" : i + 1; });
  $("locked-banner").hidden = !current.locked || current.stage === "closed";
  $("due-date").textContent = packet ? `Filing deadline · ${new Date(packet.nominal_due_date + "T00:00").toLocaleDateString(p.locale, {day: "numeric", month: "short", year: "numeric"})}*` : "Filing deadline · set when the packet is prepared";
  $("question").hidden = !(current.question && current.stage === "ready_to_prepare" && ["operator", "owner"].includes(current.role) && !current.locked);
  // Tax
  $("tax-total").textContent = money(packet?.tax_centavos); $("tax-total").classList.toggle("empty", !packet); $("value-label").textContent = p.valueLabel;
  $("property-value").textContent = current.stage === "closed" ? "—" : money(packet?.property_value_centavos ?? current.property_value_centavos);
  $("verified-share").textContent = packet ? `${packet.share_bps / 100}%` : "—"; $("gross").textContent = money(packet?.gross_centavos);
  $("allowance-label").textContent = packet?.allowance_label || "Allowance"; $("allowance").textContent = money(packet?.allowance_centavos);
  $("net").textContent = money(packet?.net_centavos); $("rate").textContent = packet?.rate_label || "—"; $("tax-fine").textContent = p.taxFine;
  $("tax-label").textContent = current.professional_hash ? "Professionally reviewed" : packet ? "Prepared · review needed" : "Awaiting evidence";
  // Evidence
  $("record-description").textContent = current.stage === "closed" ? "Deleted at case closure" : current.record ? `${p.issuer} ${p.record} · ${current.record.share_bps / 100}% share · intake reported 100%` : "Missing · intake reports 100% ownership";
  $("record-status").textContent = current.record?.version === 2 ? "Confirmed" : current.record ? "Conflict" : "Needed";
  $("record-status").className = current.record?.version === 2 ? "good-chip" : "neutral-chip";
  $("documents").textContent = (current.documents || []).map((d) => d.replace("synthetic_", "").replaceAll("_", " ")).join(", ") || "Deleted at case closure";
  $("payee").textContent = packet ? `${packet.payee} · simulated ${p.authority}` : `Simulated ${p.authority} tax payee`;
  // Offices
  const office = packet?.ecar_office, outbox = current.outbox;
  $("filing-receipt").textContent = current.filing_receipt || "Not yet verified";
  $("payment-receipt").textContent = current.payment_receipt || (current.payment_key ? "Pending · not settled" : "Not yet settled");
  $("office-name").textContent = office ? (office.rdo ? `BIR RDO ${office.rdo} · ${office.name}` : office.name) : current.stage === "closed" ? "Deleted at case closure" : "Set when the packet is prepared";
  $("office-mailbox").textContent = office?.mailbox || (office ? "None for this step" : "—");
  $("outbox-status").textContent = outbox ? "Draft ready · not sent" : office && !office.mailbox ? "Not needed" : "Prepared after payment is verified";
  $("outbox-details").hidden = !outbox; $("outbox-subject").textContent = outbox?.subject || ""; $("outbox-body").textContent = outbox?.body || "";
  $("open-steps").replaceChildren(...(current.open_steps || []).map((s) => { const li = document.createElement("li"); li.textContent = s; return li; }));
  $("office-fine").textContent = p.officeFine;
  // Impact
  $("m-mismatch").textContent = m.mismatches_caught_before_filing ?? 0; $("m-docs").textContent = m.documents_obtained_by_agent ?? 0;
  $("m-dupes").textContent = m.duplicate_actions_prevented ?? 0;
  $("m-days").textContent = m.days_filed_before_deadline != null ? `${m.days_filed_before_deadline} days` : "—";
  $("m-penalty-label").textContent = p.penaltyLabel;
  $("m-penalty").textContent = m.penalty_if_one_year_late_centavos != null ? `${money(m.penalty_if_one_year_late_centavos)} avoided` : "—";
  $("m-deleted").textContent = m.personal_data_deleted ? "Yes" : "Not yet"; $("impact-fine").textContent = p.impactFine;
  // Approval
  const professional = current.role === "professional" && current.stage === "await_professional";
  const owner = current.role === "owner" && current.stage === "await_owner";
  $("approval").hidden = !(professional || owner) || current.locked; $("code-row").hidden = !owner; $("owner-code").required = owner;
  $("code-command").textContent = `python3 -m habilin code --case ${current.id}`;
  $("confirm-text").textContent = professional ? `I reviewed the evidence, assumptions, deadline and the ${money(packet?.tax_centavos)} calculation.`
    : `I authorize this exact filing and one ${money(packet?.tax_centavos)} payment to the official ${p.authority} payee.`;
  $("packet-hash").textContent = packetHash ? `${packetHash.slice(0, 24)}…` : "";
  // Technical
  $("execution-stage").textContent = current.stage;
  $("professional-status").textContent = packetHash && current.professional_hash === packetHash ? "Recorded for current packet" : "Not recorded for current packet";
  $("owner-status").textContent = packetHash && current.owner_hash === packetHash ? "Recorded for current packet" : "Not recorded for current packet";
  $("full-packet-hash").textContent = packetHash || "Not prepared"; $("filing-key").textContent = current.submission_key || "Not dispatched";
  $("payment-key").textContent = current.payment_key || "Not dispatched"; $("balance").textContent = money(current.balance_centavos);
  $("activity-empty").hidden = current.events.length > 0;
  $("events").replaceChildren(...current.events.slice().reverse().map((event) => {
    const li = document.createElement("li"), strong = document.createElement("strong"), text = document.createElement("p"), small = document.createElement("small");
    strong.textContent = event.tool.replaceAll("_", " ");
    if (event.tool === "classify_intent") { try { const c = JSON.parse(event.result); text.textContent = `${c.intent} · ${c.source}`; } catch { text.textContent = "Classification recorded"; } }
    else text.textContent = event.result;
    small.textContent = `${new Date(event.timestamp).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit", second: "2-digit"})} · ${event.actor}`;
    li.append(strong, text, small); return li;
  }));
  // Owner controls
  $("owner-controls").hidden = current.role !== "owner" || current.stage === "closed";
  $("lock").hidden = current.role !== "owner" || current.locked;
  $("close-case").hidden = current.role !== "owner" || current.stage !== "completed";
  renderAction();
}

async function send(text) {
  if (busy) return; busy = true; $("send").disabled = true; $("next-action").disabled = true; error(""); message(text, "user"); $("message").value = "";
  try { const data = await api("/api/message", {text}); message(data.reply, "agent", [data.classification.source, data.phrased_by].filter(Boolean).join(" · ")); await refresh(); }
  catch (e) { error(e.message); message(e.message, "agent"); }
  finally { busy = false; $("send").disabled = false; if (current) renderAction(); }
}
async function tool(name, args, after) {
  if (busy) return; busy = true; error("");
  try { await api("/api/tool", {name, args}); await refresh(); if (after) message(after, "agent"); }
  catch (e) { error(e.message); } finally { busy = false; if (current) renderAction(); }
}
function showPortal(next) {
  $("case-desk").hidden = true; $("role-switch").hidden = true; $("portal").hidden = false; error("");
  document.querySelectorAll("[data-person]").forEach((b) => b.classList.toggle("next", b.dataset.person === next));
  window.scrollTo({top: 0});
}
const ONBOARDING = {
  operator: ["Maria, you run the case", ["Press the highlighted button. Habilin fetches the official records and catches mismatches.", "Answer its one question, then prepare the tax packet.", "Hand off to Atty. Cruz and Ana when Habilin says it is their turn."]],
  professional: ["Atty. Cruz, you check the numbers", ["Open “Show case details” to see the evidence and the tax math.", "Tick the box to confirm the exact packet, then record approval.", "Nothing is filed or paid without your approval."]],
  owner: ["Ana, you approve the money", ["Get your one-time code from your own device (a separate terminal in this demo).", "Enter it once to approve filing and payment to the official payee only.", "You can lock the case at any time, and close it to delete personal data."]]};
function onboard(person) {
  let seen = false; try { seen = sessionStorage.getItem("habilin.onboarded." + person) === "1"; } catch {}
  $("onboarding").hidden = seen;
  if (seen) return;
  $("onb-title").textContent = ONBOARDING[person][0];
  $("onb-steps").replaceChildren(...ONBOARDING[person][1].map((s) => { const li = document.createElement("li"); li.textContent = s; return li; }));
}
function toggleChat(open) {
  $("chat-widget").hidden = !open; $("chat-toggle").hidden = open; $("chat-toggle").setAttribute("aria-expanded", String(open));
  if (open) $("message").focus();
}
async function signIn(person) {
  $("conversation").replaceChildren(); message(PEOPLE[person][3], "agent");
  await useRole(person); onboard(person); window.scrollTo({top: 0});
}
async function useRole(next) {
  if (!tokens[next]) return;
  role = next; remember(); error("");
  $("owner-code").value = ""; $("confirm").checked = false;
  try { await refresh(); } catch (e) { error(e.message); }
}

document.querySelectorAll("[data-role]").forEach((b) => b.addEventListener("click", () => useRole(b.dataset.role)));
document.querySelectorAll("[data-case]").forEach((b) => b.addEventListener("click", async () => {
  if (busy || b.dataset.case === caseId) return;
  caseId = b.dataset.case; remember(); $("conversation").replaceChildren(); showTab("tax");
  try { await refresh(); message(`Switched to ${current.label}. Same agent, ${place().authority} rules.`, "agent"); } catch (e) { error(e.message); }
}));
document.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
$("next-action").addEventListener("click", () => {
  const action = $("next-action").dataset.action;
  if (busy || !current) return;
  if (action.startsWith("switch:")) { showPortal(action.slice(7)); return; }
  send(action === "progress" ? "Progress this estate case" : "Check case status");
});
$("answer-no").addEventListener("click", () => tool("answer_question", {answer: false}, "Thanks. That deduction does not apply, so I can prepare the packet."));
$("answer-yes").addEventListener("click", () => tool("answer_question", {answer: true}, "Thanks. That changes the tax, so I stopped the case for a professional."));
$("message-form").addEventListener("submit", (e) => { e.preventDefault(); send($("message").value); });
document.querySelectorAll("[data-message]").forEach((el) => el.addEventListener("click", () => send(el.dataset.message)));
$("approval").addEventListener("submit", (e) => {
  e.preventDefault(); const owner = current.role === "owner";
  const args = {packet_hash: packetHash, confirmed: $("confirm").checked}; if (owner) args.code = $("owner-code").value;
  $("owner-code").value = ""; $("confirm").checked = false;
  tool(owner ? "owner_approve" : "professional_approve", args, owner ? "Owner approval recorded for the exact packet. Switch to Operator to file it." : "Professional review recorded. The owner decides next.");
});
$("lock").addEventListener("click", () => tool("lock", {}));
$("close-case").addEventListener("click", () => {
  // Two clicks: deletion cannot be undone.
  if (!$("close-case").dataset.armed) { $("close-case").dataset.armed = "1"; $("close-case").textContent = "Click again to permanently delete personal data"; return; }
  delete $("close-case").dataset.armed; $("close-case").textContent = "Close case & delete personal data";
  tool("close_case", {confirmed: true});
});
$("download-packet").addEventListener("click", (e) => {
  e.preventDefault();
  // A plain one-page summary for people, printed or saved as PDF from the browser.
  const v = (id) => $(id).textContent, el = (tag, text) => { const n = document.createElement(tag); if (text != null) n.textContent = text; return n; };
  const table = (rows) => { const t = el("table"); rows.forEach(([k, val]) => { const tr = el("tr"); tr.append(el("td", k), el("td", val)); t.append(tr); }); return t; };
  const steps = el("ol"); [...$("open-steps").children].forEach((li) => steps.append(el("li", li.textContent)));
  $("print-view").replaceChildren(
    el("h1", `${v("case-name")} · ${v("case-eyebrow")}`), el("p", `Case ${v("crumb-case")} · prepared ${new Date().toLocaleDateString()} · simulated institutions, synthetic case`),
    el("h2", "Tax"), table([[v("value-label"), v("property-value")], ["Verified estate share", v("verified-share")], ["Estate’s share of value", v("gross")], [v("allowance-label"), v("allowance")], ["Taxable amount", v("net")], ["Rate", v("rate")], ["Tax due", v("tax-total")], ["Status", v("tax-label")]]),
    el("h2", "Approvals and receipts"), table([["Professional approval", v("professional-status")], ["Owner authorization", v("owner-status")], ["Filing", v("filing-receipt")], ["Payment", v("payment-receipt")], ["Packet fingerprint", v("full-packet-hash")]]),
    el("h2", "Next office"), table([["Office", v("office-name")], ["Official mailbox", v("office-mailbox")]]),
    el("h2", "Still to do"), steps, el("p", v("tax-fine")));
  window.print();
});
// Local demo: one screen plays all three people, so the page signs itself in. Owner approvals still need the one-time code.
(async () => {
  try {
    const res = await fetch("/api/demo-session"), data = await res.json();
    if (!res.ok) throw new Error(data.error);
    tokens = data.tokens;
    if (ROLES.includes(role)) await refresh(); else showPortal("operator");
  } catch (e) { error(`Could not open the demo case (${e.message || "server unavailable"}). Restart it with: python3 -m habilin serve`); }
})();
$("switch-user").addEventListener("click", () => showPortal());
document.querySelectorAll("[data-person]").forEach((b) => b.addEventListener("click", () => signIn(b.dataset.person)));
$("onb-done").addEventListener("click", () => { try { sessionStorage.setItem("habilin.onboarded." + role, "1"); } catch {} $("onboarding").hidden = true; });
$("chat-toggle").addEventListener("click", () => toggleChat(true));
$("chat-close").addEventListener("click", () => toggleChat(false));
