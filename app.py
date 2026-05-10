"""
app.py — Finance Credit Follow-Up AI Agent · Streamlit Dashboard
Clean, modular rewrite using Streamlit best practices.

Run with:  streamlit run app.py
"""

import streamlit as st
import time
from datetime import datetime
from langgraph.types import Command

from workflow import agent
from models import InvoiceData, AgentState

# ─────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Finance Credit Follow-Up AI Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
SAMPLE_INVOICE: InvoiceData = {
    "invoice_no":     "INV-2026-101",
    "client":         "ABC Technologies Pvt Ltd",
    "amount":         45250.75,
    "due_date":       "11 May 2026",
    "contact_email":  "finance@abctech.com",
    "followup_count": 1,
}

WORKFLOW_STEPS = [
    "Invoice Loaded",
    "Overdue Calc",
    "Stage Set",
    "Email Draft",
    "Validated",
    "Approval",
    "Dispatched",
    "Audit Log",
]

# Lightweight CSS — cards, badges, email preview, stepper
MINIMAL_CSS = """
<style>
/* ── Stepper ── */
.step-row { display: flex; gap: 0; align-items: center; margin-bottom: 1.2rem; overflow-x: auto; }
.step-item { display: flex; flex-direction: column; align-items: center; min-width: 80px; }
.step-item:not(:last-child) { flex: 1; }
.step-connector { flex: 1; height: 2px; background: #ddd; margin: 0; }
.step-circle {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .85rem; font-weight: 700; border: 2px solid #ccc;
    background: white; color: #aaa; flex-shrink: 0;
}
.step-circle.done    { background: #d1fae5; border-color: #10b981; color: #059669; }
.step-circle.active  { background: #fef3c7; border-color: #f59e0b; color: #d97706; }
.step-circle.wait    { background: #fffbeb; border-color: #f59e0b; color: #d97706;
                       box-shadow: 0 0 0 3px rgba(245,158,11,.2); }
.step-label { font-size: .6rem; margin-top: 4px; text-align: center;
              color: #6b7280; font-weight: 600; line-height: 1.3; max-width: 72px; }
.step-label.done   { color: #059669; }
.step-label.active { color: #d97706; }
.step-label.wait   { color: #d97706; }

/* ── Cards ── */
.metric-card {
    background: white; border: 1px solid #e5e7eb; border-radius: 10px;
    padding: .9rem 1.1rem; text-align: center;
}
.metric-val { font-size: 1.5rem; font-weight: 700; color: #111827; line-height: 1; }
.metric-lbl { font-size: .72rem; color: #6b7280; margin-top: 4px; text-transform: uppercase; letter-spacing: .5px; }

/* ── Email preview ── */
.email-card {
    background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden;
}
.email-header { font-color : black; background: white; border-bottom: 1px solid #e5e7eb; padding: .75rem 1.1rem; }
.email-field  { display: flex; gap: 8px; margin-bottom: 4px; font-size: .85rem; }
.email-field:last-child { margin-bottom: 0; }
.email-fl     { color: #6b7280; font-weight: 700; font-size: .7rem; text-transform: uppercase;
                letter-spacing: .5px; min-width: 58px; padding-top: 1px; }
.email-body   { padding: 1rem 1.1rem; font-size: .87rem; color: #374151;
                white-space: pre-wrap; line-height: 1.75; max-height: 300px; overflow-y: auto; }

/* ── Badges ── */
.badge { display: inline-block; padding: 2px 10px; border-radius: 20px;
         font-size: .7rem; font-weight: 700; letter-spacing: .4px; }
.badge-idle     { background: #f3f4f6; color: #6b7280; }
.badge-running  { background: #fef3c7; color: #d97706; }
.badge-wait     { background: #fff7ed; color: #ea580c; }
.badge-complete { background: #d1fae5; color: #059669; }

/* ── Activity log ── */
.log-entry { display: flex; gap: 8px; font-size: .8rem; padding: 5px 0;
             border-bottom: 1px solid #f3f4f6; }
.log-time  { color: #9ca3af; font-family: monospace; flex-shrink: 0; }
.log-msg   { color: #374151; }

/* ── Result boxes ── */
.result-sent     { font-color : black; background: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 10px; padding: 1.2rem; }
.result-escalate { font-color : black; background: #fff1f2; border: 1px solid #fca5a5; border-radius: 10px; padding: 1.2rem; }
.result-nodue    { font-color : black; background: #f0fdf4; border: 1px solid #86efac; border-radius: 10px; padding: 1.2rem; }
</style>
"""


# ═════════════════════════════════════════════
#  SESSION STATE
# ═════════════════════════════════════════════

def init_session():
    """Initialise all session state keys with sensible defaults."""
    defaults = {
        "wf_status":         "idle",    # idle | pending | interrupt | resuming | complete
        "output_state":      None,
        "config":            None,
        "initial_state":     None,
        "interrupt_payload": None,
        "resume_data":       None,
        "activity_log":      [],
        "invoice":           dict(SAMPLE_INVOICE),
        "balloons_shown":    False,
        "rejection_count":   0,
        # Sidebar form fields — keys must match widget key= params
        "edit_inv_no":       SAMPLE_INVOICE["invoice_no"],
        "edit_client":       SAMPLE_INVOICE["client"],
        "edit_amount":       float(SAMPLE_INVOICE["amount"]),
        "edit_due_date":     SAMPLE_INVOICE["due_date"],
        "edit_email":        SAMPLE_INVOICE["contact_email"],
        "edit_fc":           int(SAMPLE_INVOICE["followup_count"]),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ═════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════

def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def add_log(icon: str, msg: str):
    st.session_state.activity_log.append({"time": now(), "icon": icon, "msg": msg})


def sync_logs(output_state: dict):
    """Replay agent output into the activity log (idempotent)."""
    if not output_state:
        return
    seen = {e["msg"] for e in st.session_state.activity_log}

    def push(icon, msg):
        if msg not in seen:
            add_log(icon, msg)
            seen.add(msg)

    inv = output_state.get("invoice", st.session_state.invoice)
    push("📋", f"Invoice {inv['invoice_no']} loaded — {inv['client']}")

    if "days_overdue" in output_state:
        d = output_state["days_overdue"]
        push("📅", "Invoice is current — not overdue" if d == 0
             else f"Invoice is {d} day{'s' if d != 1 else ''} overdue")

    if output_state.get("stage_key"):
        tone = (output_state.get("stage_meta") or {}).get("tone", "")
        push("🎯", f"Stage: {output_state['stage_key']} · Tone: {tone}")

    if output_state.get("email_draft"):
        push("✉️", "AI generated personalised email draft")
        vs = output_state.get("validation_status", "")
        vf = output_state.get("validation_feedback", "")
        if vs == "approved":
            push("✅", "Draft passed automated validation")
        elif vs == "rejected" and vf:
            push("⚠️", f"Validation issue: {vf[:80]}")

    if "__interrupt__" in output_state:
        push("👤", "Workflow paused — awaiting your approval")

    if output_state.get("send_status") == "sent":
        push("📤", "Follow-up email dispatched to client")
        push("📊", "Audit log recorded — workflow complete")

    if output_state.get("escalation_required") and output_state.get("send_status") == "not_sent":
        err = output_state.get("send_error", "")
        if "not overdue" not in err.lower():
            push("🚨", "Escalated to finance manager for manual review")
            push("📊", "Audit log recorded — workflow complete")

    if (output_state.get("audit_log")
            and output_state.get("send_status") == "not_sent"
            and not output_state.get("escalation_required")):
        push("✅", "Invoice not overdue — no action taken")
        push("📊", "Audit log recorded — workflow complete")


def full_email_text(draft) -> str:
    """Combine greeting / body / closing from an email draft object."""
    parts = [
        getattr(draft, "greeting", "") or "",
        getattr(draft, "body", "") or "",
        getattr(draft, "closing", "") or "",
    ]
    return "\n\n".join(p.strip() for p in parts if p.strip())


# ═════════════════════════════════════════════
#  STEP STATUS MAPPING
# ═════════════════════════════════════════════

def get_step_statuses(output_state, wf_status: str) -> list[str]:
    """Return a status string for each of the 8 workflow steps."""
    # Status values: "" (pending) | "active" | "done" | "wait"
    if output_state is None or wf_status == "idle":
        return [""] * 8

    s = [""] * 8

    s[0] = "done"  # Invoice Loaded — always done if we have output

    has_overdue = "days_overdue" in output_state
    s[1] = "done" if has_overdue else "active"

    has_stage = "stage_key" in output_state
    s[2] = "done" if has_stage else ("active" if has_overdue else "")

    has_draft  = output_state.get("email_draft") is not None
    no_overdue = has_stage and output_state.get("stage_key") is None
    s[3] = "done" if (has_draft or no_overdue) else ("active" if has_stage else "")

    has_val = "validation_status" in output_state
    s[4] = "done" if has_val else ("active" if has_draft else "")

    has_send = "send_status" in output_state
    if wf_status == "interrupt":
        s[5] = "wait"
    elif has_send or no_overdue:
        s[5] = "done"
    elif has_val:
        s[5] = "active"

    s[6] = "done" if has_send else ("active" if s[5] == "done" else "")

    has_audit = output_state.get("audit_log") is not None
    s[7] = "done" if has_audit else ("active" if has_send else "")

    return s


# ═════════════════════════════════════════════
#  COMPONENTS
# ═════════════════════════════════════════════

def render_sidebar():
    """Left sidebar: invoice form, launch/reset buttons, live status details."""
    with st.sidebar:
        st.title("💰 Invoice Agent")

        wf = st.session_state.wf_status

        # ── Status indicator ──
        status_labels = {
            "idle":      ("⚪", "Idle",               "Ready to process"),
            "pending":   ("🟡", "Processing…",        "Agent is running"),
            "resuming":  ("🟡", "Resuming…",           "Continuing workflow"),
            "interrupt": ("🟠", "Awaiting Approval",  "Review email draft"),
            "complete":  ("🟢", "Complete",            "Workflow finished"),
        }
        dot, lbl, sub = status_labels.get(wf, ("⚪", "—", ""))
        st.markdown(f"**Status:** {dot} {lbl}  \n*{sub}*")
        st.divider()

        # ── Invoice fields ──
        st.subheader("Invoice Configuration")
        locked = wf in ("pending", "resuming", "interrupt")
        if locked:
            st.caption("⚠️ Fields locked while agent is running.")

        st.text_input("Invoice No.",   disabled=locked, key="edit_inv_no")
        st.text_input("Client Name",   disabled=locked, key="edit_client")
        st.number_input("Amount (₹)",  min_value=0.0, step=500.0,
                        format="%.2f", disabled=locked, key="edit_amount")
        st.number_input("Follow-up #", min_value=0, max_value=10,
                        disabled=locked, key="edit_fc")
        st.text_input("Due Date",      help="e.g. 11 May 2026",
                      disabled=locked, key="edit_due_date")
        st.text_input("Contact Email", disabled=locked, key="edit_email")

        st.markdown("&nbsp;", unsafe_allow_html=True)

        # ── Buttons ──
        btn_disabled = wf in ("pending", "resuming", "interrupt")
        btn_label    = "🚀 Launch AI Agent" if wf in ("idle", "complete") else "⟳ Agent Running…"

        if st.button(btn_label, use_container_width=True, type="primary",
                     disabled=btn_disabled, key="btn_launch"):
            _launch_agent()

        if wf in ("idle", "complete"):
            if st.button("🔄 Reset to Sample Invoice",
                         use_container_width=True, key="btn_reset"):
                _reset_to_sample()

        # ── Live workflow details (after first run) ──
        os = st.session_state.output_state
        if os:
            st.divider()
            st.subheader("Workflow Details")
            details = {
                "Days Overdue":  os.get("days_overdue", "—"),
                "Stage":         os.get("stage_key", "N/A") or "N/A",
                "Validation":    (os.get("validation_status") or "—").title(),
                "Retries":       f"{os.get('retry_count', 0)} / {os.get('max_retries', 3)}",
                "Dispatch":      (os.get("send_status") or "—").replace("_", " ").title(),
            }
            for k, v in details.items():
                st.caption(k)
                st.markdown(f"**{v}**")


def _launch_agent():
    """Build invoice dict and kick off the workflow."""
    new_inv: InvoiceData = {
        "invoice_no":     st.session_state.edit_inv_no,
        "client":         st.session_state.edit_client,
        "amount":         float(st.session_state.edit_amount),
        "due_date":       st.session_state.edit_due_date,
        "contact_email":  st.session_state.edit_email,
        "followup_count": int(st.session_state.edit_fc),
    }
    thread_id = f"inv-{new_inv['invoice_no']}-{int(time.time())}"
    st.session_state.update({
        "invoice":           new_inv,
        "config":            {"configurable": {"thread_id": thread_id}},
        "initial_state":     {"invoice": new_inv, "retry_count": 0, "max_retries": 3},
        "output_state":      None,
        "activity_log":      [],
        "wf_status":         "pending",
        "balloons_shown":    False,
        "rejection_count":   0,
        "interrupt_payload": None,
        "resume_data":       None,
    })
    add_log("🚀", f"Agent launched for {new_inv['invoice_no']}")
    st.rerun()


def _reset_to_sample():
    """Reset all state back to defaults."""
    st.session_state.update({
        "edit_inv_no":   SAMPLE_INVOICE["invoice_no"],
        "edit_client":   SAMPLE_INVOICE["client"],
        "edit_amount":   float(SAMPLE_INVOICE["amount"]),
        "edit_due_date": SAMPLE_INVOICE["due_date"],
        "edit_email":    SAMPLE_INVOICE["contact_email"],
        "edit_fc":       int(SAMPLE_INVOICE["followup_count"]),
        "invoice":           dict(SAMPLE_INVOICE),
        "output_state":      None,
        "activity_log":      [],
        "wf_status":         "idle",
        "balloons_shown":    False,
        "rejection_count":   0,
        "interrupt_payload": None,
        "resume_data":       None,
    })
    st.rerun()


def render_header():
    """Top bar: title, invoice summary, status badge."""
    inv = st.session_state.invoice
    wf  = st.session_state.wf_status
    badge_html = {
        "idle":      '<span class="badge badge-idle">Idle</span>',
        "pending":   '<span class="badge badge-running">⟳ Processing</span>',
        "resuming":  '<span class="badge badge-running">⟳ Resuming</span>',
        "interrupt": '<span class="badge badge-wait">⏸ Awaiting Approval</span>',
        "complete":  '<span class="badge badge-complete">✓ Complete</span>',
    }.get(wf, "")

    col_title, col_info = st.columns([2, 1])
    with col_title:
        st.markdown("## 💰 Finance Credit Follow-Up AI Agent")
        st.markdown(f"**{inv['invoice_no']}** · {inv['client']} · ₹{inv['amount']:,.2f}  {badge_html}",
                    unsafe_allow_html=True)
    with col_info:
        pass  # reserved for future additions


def render_welcome():
    """Welcome screen shown when workflow is idle."""
    inv = st.session_state.invoice

    st.info(
        "**What this agent does:** Analyses overdue invoices, generates personalised "
        "payment reminders at exactly the right tone, and routes escalations — with "
        "human-in-the-loop approval built in.",
        icon="ℹ️",
    )

    # ── Current invoice preview ──
    with st.container(border=True):
        st.markdown("#### 📋 Invoice Ready to Process")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**Invoice No.**  \n{inv['invoice_no']}")
        c1.markdown(f"**Client**  \n{inv['client']}")
        c2.metric("Amount Due", f"₹{inv['amount']:,.2f}")
        c3.markdown(f"**Due Date**  \n{inv['due_date']}")
        c3.markdown(f"**Follow-Up #**  \n{inv['followup_count']}")
        c4.markdown(f"**Contact Email**  \n{inv['contact_email']}")
        st.caption("← Edit invoice details in the sidebar, then click **🚀 Launch AI Agent**")

    # ── How it works ──
    with st.container(border=True):
        st.markdown("#### ⚡ How It Works")
        cols = st.columns(4)
        steps_info = [
            ("📅", "Analyse",  "Calculates overdue days and classifies the follow-up stage automatically"),
            ("✉️", "Generate", "AI crafts a personalised reminder with the right tone and urgency"),
            ("👤", "Approve",  "You review the draft and approve, or request revisions with feedback"),
            ("📤", "Dispatch", "Approved emails are sent with a full compliance audit trail"),
        ]
        for col, (icon, title, desc) in zip(cols, steps_info):
            with col:
                st.markdown(f"**{icon} {title}**")
                st.caption(desc)


def render_stepper(output_state, wf_status: str):
    """Horizontal step indicator showing current workflow progress."""
    statuses = get_step_statuses(output_state, wf_status)

    circles_html = ""
    for i, (label, status) in enumerate(zip(WORKFLOW_STEPS, statuses)):
        icon = "✓" if status == "done" else ("⏸" if status == "wait" else str(i + 1))
        circles_html += f'<div class="step-item">'
        circles_html += f'<div class="step-circle {status}">{icon}</div>'
        circles_html += f'<div class="step-label {status}">{label}</div>'
        circles_html += '</div>'
        if i < len(WORKFLOW_STEPS) - 1:
            circles_html += '<div class="step-connector"></div>'

    st.markdown(f'<div class="step-row">{circles_html}</div>', unsafe_allow_html=True)


def render_metrics():
    """Key invoice metrics displayed as a 4-column row."""
    inv  = st.session_state.invoice
    os   = st.session_state.output_state
    days = os.get("days_overdue", "—") if os else "—"
    stage = (os.get("stage_key") or "N/A") if os else "—"
    vstatus = (os.get("validation_status") or "—").title() if os else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Amount Due",       f"₹{inv['amount']:,.0f}")
    c2.metric("Days Overdue",     str(days))
    c3.metric("Follow-Up Stage",  stage)
    c4.metric("Draft Status",     vstatus)


def render_email_preview(ep: dict | None = None, draft=None, title: str = "Email Preview"):
    """
    Render an email preview card.
    Accepts either a dict `ep` (from interrupt payload) or
    a draft object (from output_state["email_draft"]).
    """
    if ep:
        recipient = ep.get("recipient", "")
        subject   = ep.get("subject", "")
        tone      = ep.get("tone", "")
        body_text = "\n\n".join(filter(None, [
            ep.get("greeting", "").strip(),
            ep.get("body", "").strip(),
            ep.get("closing", "").strip(),
        ]))
    elif draft:
        recipient = str(getattr(draft, "recipient", ""))
        subject   = getattr(draft, "subject", "")
        tone      = getattr(draft, "tone", "")
        body_text = full_email_text(draft)
    else:
        st.caption("No email draft available.")
        return

    st.markdown(f"##### {title}")
    st.markdown(f"""
<div class="email-card">
  <div class="email-header">
    <div class="email-field"><span class="email-fl">To</span><span>{recipient}</span></div>
    <div class="email-field"><span class="email-fl">Subject</span><strong>{subject}</strong></div>
    <div class="email-field"><span class="email-fl">Tone</span><em>{tone}</em></div>
  </div>
  <div class="email-body">{body_text}</div>
</div>
""", unsafe_allow_html=True)


def render_activity_log():
    """Chronological activity feed — most recent first."""
    logs = st.session_state.activity_log
    if not logs:
        st.caption("No activity yet.")
        return
    for entry in reversed(logs[-14:]):
        st.markdown(
            f'<div class="log-entry">'
            f'<span class="log-time">{entry["time"]}</span>'
            f'<span>{entry["icon"]}</span>'
            f'<span class="log-msg">{entry["msg"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_approval_panel():
    """Human-in-the-loop review panel shown during interrupt."""
    payload   = st.session_state.interrupt_payload
    os        = st.session_state.output_state or {}
    rej_cnt   = st.session_state.rejection_count
    retry_cnt = os.get("retry_count", 0)
    max_retry = os.get("max_retries", 3)

    if not payload:
        st.warning("No approval payload found.")
        return

    ep = payload.get("email_preview", {})

    st.markdown("### 👤 Your Approval Required")
    st.caption("Review the AI-generated email draft before it is dispatched.")

    if rej_cnt > 0:
        st.info(f"⟳ AI regenerated this draft based on your earlier feedback ({rej_cnt} revision{'s' if rej_cnt != 1 else ''}).")

    render_email_preview(ep=ep, title="Generated Email Draft")

    st.markdown("---")
    col_a, col_r = st.columns(2)

    with col_a:
        st.success("**✓ Approve & Send**  \nEmail is dispatched immediately to the client.")
        if st.button("✓ Approve Email", use_container_width=True, type="primary", key="btn_approve"):
            add_log("✅", "Email approved — dispatching now")
            st.session_state.resume_data = {"decision": "approve", "feedback": ""}
            st.session_state.wf_status   = "resuming"
            st.rerun()

    with col_r:
        st.error("**✗ Reject & Revise**  \nAI regenerates based on your feedback.")
        feedback = st.text_area(
            "Revision feedback (required when rejecting):",
            placeholder="e.g. Make tone more urgent, mention late fee, shorten subject…",
            height=90,
            key="rej_feedback",
        )
        if st.button("✗ Request Revision", use_container_width=True, type="secondary", key="btn_reject"):
            fb = feedback.strip() or "User requested changes to the email draft."
            add_log("✗", f"Revision requested: {fb[:70]}{'…' if len(fb) > 70 else ''}")
            st.session_state.rejection_count += 1
            st.session_state.resume_data = {"decision": "reject", "feedback": fb}
            st.session_state.wf_status   = "resuming"
            st.rerun()

    remaining = max_retry - retry_cnt
    if 0 <= remaining <= 1:
        st.warning(
            f"⚠️ Only **{remaining}** revision attempt{'s' if remaining != 1 else ''} remaining "
            "before automatic escalation to the finance manager."
        )


def render_results():
    """Final result panel — sent, escalated, or not overdue."""
    os    = st.session_state.output_state
    if not os:
        return

    send  = os.get("send_status", "")
    esc   = os.get("escalation_required", False)
    draft = os.get("email_draft")
    days  = os.get("days_overdue", 0)
    inv   = st.session_state.invoice

    # Trigger confetti once on success
    if send == "sent" and not st.session_state.balloons_shown:
        st.balloons()
        st.session_state.balloons_shown = True

    # ── Not overdue ──
    if days == 0:
        st.markdown(f"""
<div class="result-nodue">
  <strong style="font-size:1.1rem">✅ Invoice Not Overdue</strong><br>
  No follow-up action required. Invoice <strong>{inv['invoice_no']}</strong> for
  <strong>{inv['client']}</strong> is not yet due (due {inv['due_date']}).
</div>
""", unsafe_allow_html=True)
        return

    # ── Sent successfully ──
    if send == "sent":
        st.markdown("""
<div class="result-sent">
  <strong style="font-size:1.1rem">📤 Email Successfully Dispatched</strong><br>
  Payment follow-up has been delivered to the client's inbox.
</div>
""", unsafe_allow_html=True)
        if draft:
            st.markdown("<br>", unsafe_allow_html=True)
            render_email_preview(draft=draft, title="Sent Email")
        return

    # ── Escalated ──
    if esc or send == "not_sent":
        err = os.get("send_error", "")
        if "not overdue" in err.lower():
            return
        reason = err or (
            f"Invoice {inv['invoice_no']} is {days} days overdue and has "
            "exceeded the automated follow-up threshold."
        )
        stage_key = os.get("stage_key", "Escalation Flag")
        st.markdown(f"""
<div class="result-escalate">
  <strong style="font-size:1.1rem">🚨 Escalated to Finance Manager</strong><br>
  Manual review required — escalation alert dispatched.<br><br>
  <strong>Reason:</strong> {reason}<br>
  <strong>Manager:</strong> finance.manager@company.com<br>
  <strong>Invoice:</strong> {inv['invoice_no']} &nbsp;·&nbsp;
  <strong>Stage:</strong> {stage_key}
</div>
""", unsafe_allow_html=True)


def render_audit_log():
    """Expandable compliance audit log panel."""
    os = st.session_state.output_state
    if not os or not os.get("audit_log"):
        return
    with st.expander("📊 Compliance Audit Log", expanded=False):
        audit = os["audit_log"]
        rows = {k.replace("_", " ").title(): v for k, v in audit.items()}
        for k, v in rows.items():
            if isinstance(v, bool):
                v_str = "✅ Yes" if v else "✗ No"
            elif v is None or v == "":
                v_str = "—"
            else:
                v_str = str(v)
            st.text(f"{k:<30}  {v_str}")


# ═════════════════════════════════════════════
#  AGENT EXECUTION
# ═════════════════════════════════════════════

def execute_initial():
    """Run the agent from the start; update state on completion."""
    with st.spinner("🤖 AI Agent Processing — Analysing invoice · Setting stage · Crafting email draft…"):
        try:
            output_state = agent.invoke(
                st.session_state.initial_state,
                config=st.session_state.config,
            )
        except Exception as exc:
            st.error(f"**Agent error:** {exc}")
            st.session_state.wf_status = "idle"
            return

    sync_logs(output_state)
    st.session_state.output_state = output_state

    if "__interrupt__" in output_state:
        st.session_state.wf_status         = "interrupt"
        st.session_state.interrupt_payload = output_state["__interrupt__"][0].value
    else:
        st.session_state.wf_status = "complete"

    st.rerun()


def execute_resume():
    """Resume the agent after a human decision; update state on completion."""
    with st.spinner("🔄 Continuing workflow — Processing your decision…"):
        try:
            output_state = agent.invoke(
                Command(resume=st.session_state.resume_data),
                config=st.session_state.config,
            )
        except Exception as exc:
            st.error(f"**Resume error:** {exc}")
            st.session_state.wf_status = "idle"
            return

    st.session_state.resume_data = None
    sync_logs(output_state)
    st.session_state.output_state = output_state

    if "__interrupt__" in output_state:
        st.session_state.wf_status         = "interrupt"
        st.session_state.interrupt_payload = output_state["__interrupt__"][0].value
        add_log("✉️", "New draft ready — please review again")
    else:
        st.session_state.wf_status = "complete"

    st.rerun()


# ═════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════

def main():
    st.markdown(MINIMAL_CSS, unsafe_allow_html=True)
    init_session()

    wf = st.session_state.wf_status

    # ── Sidebar is always visible ──
    render_sidebar()

    # ── Header ──
    render_header()
    st.divider()

    # ── Idle welcome screen ──
    if wf == "idle":
        render_welcome()
        return

    # ── Running states: show stepper then block on execution ──
    render_stepper(st.session_state.output_state, wf)

    if wf in ("pending", "resuming"):
        if st.session_state.output_state:
            render_metrics()
        if wf == "pending":
            execute_initial()
        else:
            execute_resume()
        return   # execution calls st.rerun(); nothing below runs

    # ── Interrupt / Complete — show full dashboard ──
    render_metrics()
    st.markdown("&nbsp;", unsafe_allow_html=True)

    col_main, col_log = st.columns([3, 1.5])

    with col_main:
        if wf == "interrupt":
            render_approval_panel()
        elif wf == "complete":
            render_results()
            render_audit_log()

    with col_log:
        st.markdown("#### 📡 Live Activity Feed")
        render_activity_log()


main()