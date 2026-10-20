let token = "";
let current;
let packetHash;
let busy = false;
const $ = (id) => document.getElementById(id);
const money = (value) => value == null ? "—" : new Intl.NumberFormat("en-PH", {style:"currency",currency:"PHP",maximumFractionDigits:0}).format(value/100);
const stages = {
  missing_record:["Obtain the missing ownership record","I’ll request a certified title copy from the simulated Registry of Deeds, compare it with the intake and resolve discrepancies.","Evidence needed",0],
  await_professional:["Ready for professional review","The certified title shows 50% co-ownership with a living sibling. A professional must confirm the assumptions, evidence and exact packet.","Review required",1],
  await_owner:["The owner has the next decision","The professional has reviewed the packet. The owner must authorize this filing and the exact tax payment with a one-time code.","Owner approval",2],
  ready_to_submit:["Authorized and ready to submit","Both approvals bind this packet and the official tax payee. The agent can now execute the authorized step.","Authorized",3],
  filing_unknown:["Check the filing before retrying","The simulated service timed out after receiving the packet. The agent will check its existing submission key to avoid a duplicate.","Outcome unknown",3],
  payment_pending:["Verify the payment in the ledger","The filing receipt is confirmed. PHP150,000 was debited once; settlement is still pending.","Payment pending",4],
  completed:["Filing and payment verified","The simulated service confirms the filing and the ledger confirms settlement. Government review, eCAR and title transfer remain open.","Milestone complete",5],
  closed:["Case closed · personal data deleted","Records, documents and messages were deleted. Only receipts and approval fingerprints remain as proof of what was filed and paid.","Closed",5],
  blocked_professional:["A legal issue needs a person","The issuer reports disputed ownership. The workflow is stopped for professional handling.","Stopped for review",0],
};
let viewPreference = "auto";
try { viewPreference = localStorage.getItem("habilin.workspace-view") || "auto"; } catch {}
if (!["auto", "guided", "professional"].includes(viewPreference)) viewPreference = "auto";
function applyView() {
  const professional = viewPreference === "professional" || (viewPreference === "auto" && current?.role === "professional");
  document.body.dataset.view = professional ? "professional" : "guided";
  $("workspace-view").value = viewPreference;
  $("view-name").textContent = professional ? "PROFESSIONAL WORKSPACE" : "GUIDED WORKSPACE";
  $("view-description").textContent = professional
    ? "Evidence, calculations, authorization and execution state in one workspace."
    : "One clear next step, with the details available whenever you need them.";
  $("calculation-details").open = professional;
  $("activity-details").open = professional;
}
$("workspace-view").addEventListener("change", () => {
  viewPreference = $("workspace-view").value;
  try { localStorage.setItem("habilin.workspace-view", viewPreference); } catch {}
  applyView();
});
applyView();
function renderAction() {
  const review = !$("approval").hidden;
  const canProgress = ["operator", "owner"].includes(current.role) && !current.locked;
  const actions = {
    missing_record: "Obtain evidence & prepare packet ↗",
    ready_to_submit: "Submit approved packet ↗",
    filing_unknown: "Reconcile filing & progress payment ↗",
    payment_pending: "Verify payment settlement ↗",
  };
  $("next-action").textContent = review ? "Review & approve this packet ↓" : canProgress && actions[current.stage] || "Check recorded case status ↗";
  $("next-action").dataset.action = review ? "review" : canProgress && actions[current.stage] ? "progress" : "status";
  $("next-action").disabled = busy;
  $("action-help").textContent = review ? "Review the source evidence and exact amount before confirming below."
    : current.locked ? "The owner safety lock blocks changes. You can still check recorded status."
    : current.stage === "await_professional" ? "Waiting for a separate professional session to review the packet."
    : current.stage === "await_owner" ? "Waiting for the owner's approval and separate one-time code."
    : current.stage === "blocked_professional" ? "Disputed ownership requires professional handling outside this demo."
    : !canProgress ? "Your professional session can review packets. An operator or owner progresses execution."
    : current.stage === "completed" ? "The sandbox milestone is complete. Government review, eCAR and title transfer remain open."
    : "This runs the next permitted sandbox steps and pauses at the next approval or uncertain result.";
}
async function api(path, body) {
  const res = await fetch(path,{method:body?"POST":"GET",headers:{"Authorization":`Bearer ${token}`,"Content-Type":"application/json"},body:body?JSON.stringify(body):undefined});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Operation failed.");
  return data;
}
function error(message) { $("error").textContent=message; $("error").hidden=!message; }
function message(text, who, source) {
  const div=document.createElement("div"); div.className=`message ${who}`; div.textContent=text;
  if(source){const small=document.createElement("small");small.textContent=source;div.append(small);}
  $("conversation").append(div); $("conversation").scrollTop=$("conversation").scrollHeight;
}
async function refresh() {
  const data=await api("/api/state");current=data.case;packetHash=data.packet_hash;
  $("login").hidden=true;$("case-desk").hidden=false;$("logout").hidden=false;
  $("session-label").textContent=`${current.role[0].toUpperCase()+current.role.slice(1)} session`;
  $("model-mode").textContent=data.mode;
  const [title,description,chip,step]=stages[current.stage] || ["Case remains open","Check the recorded activity.","In progress",0];
  $("stage-title").textContent=title;$("stage-description").textContent=description;$("stage-chip").textContent=chip;
  document.querySelectorAll("[data-step]").forEach((el,i)=>{el.className=i<step?"done":i===step?"current":"";el.querySelector("i").textContent=i<step?"✓":"—";});
  $("locked-banner").hidden=!current.locked;
  const packet=current.packet;
  $("tax-total").textContent=money(packet?.tax_centavos);$("gross").textContent=money(packet?.gross_centavos);$("net").textContent=money(packet?.net_centavos);
  $("verified-share").textContent=packet?`${packet.share_bps/100}%`:"—";
  $("tax-label").textContent=current.professional_hash?"Professionally reviewed":packet?"Prepared · review needed":"Awaiting evidence";
  $("case-name").textContent=current.label;
  $("record-description").textContent=current.stage==="closed"?"Deleted at case closure":current.record?`Issuer version ${current.record.version} · ${current.record.share_bps/100}% share · intake reported 100%`:"Missing · intake reports 100% ownership";
  $("record-status").textContent=current.record?.version===2?"Corrected":current.record?"Conflict":"Needed";
  $("record-status").className=current.record?.version===2?"good-chip":"neutral-chip";
  $("filing-receipt").textContent=current.filing_receipt||"Not yet verified";
  $("payment-receipt").textContent=current.payment_receipt|| (current.payment_key?"Pending · not settled":"Not yet settled");
  $("balance").textContent=money(current.balance_centavos);
  const office=current.packet?.ecar_office, outbox=current.outbox, m=current.metrics||{};
  $("office-name").textContent=office?`RDO ${office.rdo} · ${office.name}`:current.stage==="closed"?"Deleted at case closure":"Set when the packet is prepared";
  $("office-mailbox").textContent=office?.mailbox||"—";
  $("outbox-status").textContent=outbox?"Draft ready · not sent":"Prepared after payment is verified";
  $("outbox-details").hidden=!outbox;$("outbox-subject").textContent=outbox?.subject||"";$("outbox-body").textContent=outbox?.body||"";
  $("m-mismatch").textContent=m.mismatches_caught_before_filing??0;$("m-docs").textContent=m.documents_obtained_by_agent??0;
  $("m-dupes").textContent=m.duplicate_actions_prevented??0;
  $("m-days").textContent=m.days_filed_before_deadline!=null?`${m.days_filed_before_deadline} days`:"—";
  $("m-penalty").textContent=m.penalty_if_one_year_late_centavos!=null?`${money(m.penalty_if_one_year_late_centavos)} avoided`:"—";
  $("m-deleted").textContent=m.personal_data_deleted?"Yes":"Not yet";
  const professional=current.role==="professional"&&current.stage==="await_professional";
  const owner=current.role==="owner"&&current.stage==="await_owner";
  $("approval").hidden=!(professional||owner)||current.locked;$("code-row").hidden=!owner;$("owner-code").required=owner;
  $("approval-title").textContent=professional?"Professional review":"Authorize filing and payment";
  $("approval-description").textContent=professional?"Confirm that the corrected source, CPA statement and restricted tax assumptions support this exact packet.":"Authorize one simulated filing and one payment of PHP150,000 to SIM-BIR-ESTATE-TAX. This does not authorize eCAR or title transfer.";
  $("confirm-text").textContent=professional?"I have reviewed the evidence, eligibility, nominal deadline and PHP150,000 calculation.":"I authorize this exact packet and PHP150,000 payment to the verified simulated tax authority.";
  $("packet-hash").textContent=packetHash?`${packetHash.slice(0,24)}…`:"";
  $("execution-stage").textContent=current.stage;
  $("professional-status").textContent=packetHash&&current.professional_hash===packetHash?"Recorded for current packet":"Not recorded for current packet";
  $("owner-status").textContent=packetHash&&current.owner_hash===packetHash?"Recorded for current packet":"Not recorded for current packet";
  $("full-packet-hash").textContent=packetHash||"Not prepared";
  $("filing-key").textContent=current.submission_key||"Not dispatched";
  $("payment-key").textContent=current.payment_key||"Not dispatched";
  renderAction();
  if (document.body.dataset.role !== current.role) {
    document.body.dataset.role = current.role;
    applyView();
  }
  $("lock").hidden=current.role!=="owner"||current.locked;
  $("close-case").hidden=current.role!=="owner"||current.stage!=="completed";
  $("event-count").textContent=`${current.events.length} EVENTS`;$("activity-empty").hidden=current.events.length>0;
  $("events").replaceChildren(...current.events.slice().reverse().map(event=>{
    const li=document.createElement("li"),strong=document.createElement("strong"),p=document.createElement("p"),small=document.createElement("small");
    strong.textContent=event.tool.replaceAll("_"," ");
    if(event.tool==="classify_intent"){try{const c=JSON.parse(event.result);p.textContent=`${c.intent} · ${c.source}`;}catch{p.textContent="Classification recorded";}}
    else p.textContent=event.result;
    small.textContent=`${new Date(event.timestamp).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit",second:"2-digit"})} · ${event.actor}`;
    li.append(strong,p,small);return li;
  }));
}
async function send(text) {
  if(busy)return;busy=true;$("send").disabled=true;$("next-action").disabled=true;error("");message(text,"user");$("message").value="";
  try{const data=await api("/api/message",{text});message(data.reply,"agent",data.classification.source);await refresh();}
  catch(e){error(e.message);message(e.message,"agent");}
  finally{busy=false;$("send").disabled=false;if(current)renderAction();}
}
$("login-form").addEventListener("submit",async(e)=>{e.preventDefault();token=$("token").value.trim();try{await refresh();$("token").value="";error("");}catch(e){token="";error(e.message);}});
$("logout").addEventListener("click",()=>{token="";current=null;delete document.body.dataset.role;applyView();$("case-desk").hidden=true;$("login").hidden=false;$("logout").hidden=true;$("session-label").textContent="Signed out";$("owner-code").value="";$("confirm").checked=false;$("conversation").replaceChildren();message("This is a new authenticated session. I can check the case or progress its next authorized step.","agent");});
$("next-action").addEventListener("click",()=>{
  if(busy||!current)return;
  if($("next-action").dataset.action==="review") {
    $("approval").scrollIntoView({block:"center"});$("confirm").focus({preventScroll:true});
  } else send($("next-action").dataset.action==="progress"?"Progress this estate case":"Check case status");
});
$("message-form").addEventListener("submit",e=>{e.preventDefault();send($("message").value);});
document.querySelectorAll("[data-message]").forEach(el=>el.addEventListener("click",()=>send(el.dataset.message)));
$("approval-form").addEventListener("submit",async(e)=>{
  e.preventDefault();if(busy)return;busy=true;error("");$("approve-button").disabled=true;$("next-action").disabled=true;
  const owner=current.role==="owner";const args={packet_hash:packetHash,confirmed:$("confirm").checked};if(owner)args.code=$("owner-code").value;
  try{await api("/api/tool",{name:owner?"owner_approve":"professional_approve",args});$("owner-code").value="";$("confirm").checked=false;await refresh();message(owner?"Owner approval recorded for the exact packet. I can now progress the authorized filing.":"Professional review recorded. The owner has the next decision.","agent");}
  catch(e){error(e.message);}finally{busy=false;$("approve-button").disabled=false;if(current)renderAction();}
});
$("lock").addEventListener("click",async()=>{try{await api("/api/tool",{name:"lock",args:{}});await refresh();}catch(e){error(e.message);}});
$("close-case").addEventListener("click",async()=>{
  // Two clicks: deletion cannot be undone.
  if(!$("close-case").dataset.armed){$("close-case").dataset.armed="1";$("close-case").textContent="Click again to permanently delete personal data";return;}
  try{await api("/api/tool",{name:"close_case",args:{confirmed:true}});await refresh();}catch(e){error(e.message);}
});
$("download-packet").addEventListener("click",async(e)=>{e.preventDefault();try{const packet=await api("/api/packet"),url=URL.createObjectURL(new Blob([JSON.stringify(packet,null,2)],{type:"application/json"})),a=document.createElement("a");a.href=url;a.download="Habilin-EST-001-Simulated-Packet.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){error(e.message);}});
