"""
app.py — Streamlit Frontend for Finance Credit Follow-Up AI Agent
=================================================================
Production-grade UI that wraps the LangGraph-powered invoice follow-up
workflow defined in main.py. Provides invoice input, human-in-the-loop
approval, live status monitoring, audit log display, and final summary.
"""

import uuid
import streamlit as st
from datetime import datetime,timezone

from workflow import agent
from models import InvoiceData, AgentState
from langgraph.types import Command

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Finance Credit Follow-Up AI Agent",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — enterprise dashboard aesthetic
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* ── Google Fonts ─────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    /* ── Global reset ─────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* ── App background ───────────────────────────────────────────────── */
    .stApp {
        background: #0f1117;
        color: #e2e8f0;
    }

    /* ── Main container ───────────────────────────────────────────────── */
    .block-container {
        padding: 2rem 3rem 3rem 3rem;
        max-width: 1400px;
    }

    /* ── Sidebar ──────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #161b27 !important;
        border-right: 1px solid #1e2a3a;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 1.5rem 1.25rem;
    }

    /* ── Hero header ──────────────────────────────────────────────────── */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa 0%, #818cf8 50%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
        line-height: 1.2;
    }
    .hero-sub {
        font-size: 1rem;
        color: #64748b;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* ── Section headers ──────────────────────────────────────────────── */
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 1.75rem 0 0.75rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: #1e2a3a;
        margin-left: 0.5rem;
    }

    /* ── Cards ────────────────────────────────────────────────────────── */
    .card {
        background: #161b27;
        border: 1px solid #1e2a3a;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .card-accent {
        border-left: 3px solid #60a5fa;
    }
    .card-success {
        border-left: 3px solid #34d399;
        background: #0d1f18;
    }
    .card-warning {
        border-left: 3px solid #fbbf24;
        background: #1c1a0d;
    }
    .card-danger {
        border-left: 3px solid #f87171;
        background: #1f0d0d;
    }

    /* ── Action banner cards ──────────────────────────────────────────── */
    .action-banner {
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .action-banner-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .action-banner-body {
        font-size: 0.88rem;
        line-height: 1.6;
        margin-bottom: 0.75rem;
    }
    .action-banner-detail-row {
        display: flex;
        gap: 0.5rem;
        align-items: flex-start;
        font-size: 0.83rem;
        margin-top: 0.3rem;
    }
    .action-banner-detail-label {
        font-weight: 700;
        min-width: 90px;
        flex-shrink: 0;
    }
    .action-banner-detail-value {
        font-family: 'DM Mono', monospace;
    }

    /* ── Email preview ────────────────────────────────────────────────── */
    .email-card {
        background: #0d1117;
        border: 1px solid #1e2a3a;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        font-family: 'DM Sans', sans-serif;
    }
    .email-meta-row {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        margin-bottom: 0.4rem;
        font-size: 0.88rem;
    }
    .email-meta-label {
        color: #475569;
        font-weight: 600;
        min-width: 70px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 0.75rem;
    }
    .email-meta-value {
        color: #cbd5e1;
        font-weight: 500;
    }
    .email-divider {
        border: none;
        border-top: 1px solid #1e2a3a;
        margin: 1rem 0;
    }
    .email-body {
        color: #e2e8f0;
        font-size: 0.92rem;
        line-height: 1.75;
        white-space: pre-wrap;
        font-family: 'DM Mono', monospace;
    }

    /* ── Tone badge ───────────────────────────────────────────────────── */
    .tone-badge {
        display: inline-block;
        padding: 0.2rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .tone-friendly   { background: #1e3a2f; color: #34d399; border: 1px solid #34d399; }
    .tone-firm       { background: #1c2a3a; color: #60a5fa; border: 1px solid #60a5fa; }
    .tone-urgent     { background: #2a1c0d; color: #fbbf24; border: 1px solid #fbbf24; }
    .tone-escalation { background: #2a0d0d; color: #f87171; border: 1px solid #f87171; }
    .tone-default    { background: #1e2a3a; color: #94a3b8; border: 1px solid #94a3b8; }

    /* ── Status pills ─────────────────────────────────────────────────── */
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.8rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    .pill-green  { background: #0d2018; color: #34d399; border: 1px solid #34d399; }
    .pill-blue   { background: #0d1a2e; color: #60a5fa; border: 1px solid #60a5fa; }
    .pill-yellow { background: #1f1a08; color: #fbbf24; border: 1px solid #fbbf24; }
    .pill-red    { background: #1f0d0d; color: #f87171; border: 1px solid #f87171; }
    .pill-gray   { background: #1a1e28; color: #94a3b8; border: 1px solid #475569; }

    /* ── Sidebar info rows ────────────────────────────────────────────── */
    .sidebar-info-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #1e2a3a;
        font-size: 0.83rem;
    }
    .sidebar-info-label { color: #475569; font-weight: 500; }
    .sidebar-info-value { color: #e2e8f0; font-weight: 600; font-family: 'DM Mono', monospace; }

    /* ── Workflow steps (sidebar) ─────────────────────────────────────── */
    .workflow-step {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 0.4rem 0;
        font-size: 0.82rem;
        color: #94a3b8;
    }
    .step-num {
        background: #1e2a3a;
        color: #60a5fa;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 1px;
    }

    /* ── Feature tags ─────────────────────────────────────────────────── */
    .feature-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.75rem;
    }
    .feature-tag {
        background: #1a2030;
        border: 1px solid #1e2a3a;
        color: #94a3b8;
        padding: 0.3rem 0.75rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 500;
    }

    /* ── Streamlit component overrides ───────────────────────────────── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1a2030 !important;
        border: 1px solid #1e2a3a !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96,165,250,0.12) !important;
    }

    div[data-testid="stForm"] {
        background: #161b27;
        border: 1px solid #1e2a3a;
        border-radius: 12px;
        padding: 1.5rem;
    }

    .stButton > button {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        opacity: 0.88 !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="secondary"] {
        background: #1e2a3a !important;
        color: #94a3b8 !important;
        border: 1px solid #2d3f54 !important;
    }

    .stExpander {
        background: #161b27 !important;
        border: 1px solid #1e2a3a !important;
        border-radius: 10px !important;
    }
    .stExpander header {
        font-weight: 600 !important;
        color: #94a3b8 !important;
    }

    .stMetric {
        background: #161b27;
        border: 1px solid #1e2a3a;
        border-radius: 10px;
        padding: 1rem 1.25rem;
    }
    [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 1.4rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }

    div.stAlert {
        border-radius: 10px !important;
    }

    /* ── Divider ──────────────────────────────────────────────────────── */
    hr { border-color: #1e2a3a; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ──────────────────────────────────────────────────────────────────────────────

_SESSION_DEFAULTS: dict = {
    "initial_state": None,
    "output_state": None,
    "config": None,
    "thread_id": None,
    "interrupt_payload": None,
    "current_email_preview": None,
    "workflow_completed": False,
    "reject_feedback": "",
    "agent_running": False,
}

for _key, _default in _SESSION_DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ──────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def reset_session() -> None:
    """Clear all session state keys back to defaults."""
    for key, default in _SESSION_DEFAULTS.items():
        st.session_state[key] = default


def build_initial_state(
    invoice_no: str,
    client: str,
    amount: float,
    due_date: str,
    contact_email: str,
    followup_count: int,
    max_retries: int,
) -> AgentState:
    """Construct the LangGraph AgentState from raw form inputs."""
    invoice: InvoiceData = {
        "invoice_no": invoice_no.strip(),
        "client": client.strip(),
        "amount": amount,
        "due_date": due_date.strip(),
        "contact_email": contact_email.strip(),
        "followup_count": followup_count,
    }
    state: AgentState = {
        "invoice": invoice,
        "retry_count": 0,
        "max_retries": max_retries,
    }
    return state


def run_agent(initial_state: AgentState, config: dict) -> dict:
    """
    Invoke the LangGraph agent with the given state and configuration.
    Returns the output state dict (may contain __interrupt__ key).
    """
    return agent.invoke(initial_state, config=config)


def resume_agent(decision: str, feedback: str, config: dict) -> dict:
    """
    Resume a paused (interrupted) LangGraph workflow with the human decision.
    Returns the new output state dict.
    """
    return agent.invoke(
        Command(resume={"decision": decision, "feedback": feedback}),
        config=config,
    )


def _tone_badge_html(tone: str) -> str:
    """Return an HTML tone badge string for the given tone label."""
    tone_lower = (tone or "").lower()
    css_class = "tone-default"
    if "friendly" in tone_lower or "gentle" in tone_lower:
        css_class = "tone-friendly"
    elif "firm" in tone_lower or "formal" in tone_lower:
        css_class = "tone-firm"
    elif "urgent" in tone_lower or "strong" in tone_lower:
        css_class = "tone-urgent"
    elif "escalat" in tone_lower or "legal" in tone_lower:
        css_class = "tone-escalation"
    return f'<span class="tone-badge {css_class}">{tone}</span>'


def _pill_html(text: str, color: str = "gray") -> str:
    """Return a small coloured pill HTML element."""
    cls_map = {
        "green": "pill-green",
        "blue": "pill-blue",
        "yellow": "pill-yellow",
        "red": "pill-red",
        "gray": "pill-gray",
    }
    css = cls_map.get(color, "pill-gray")
    return f'<span class="status-pill {css}">{text}</span>'


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    """Render the sidebar with app info, workflow steps, and session state."""
    with st.sidebar:
        # App branding
        st.markdown(
            """
            <div style="margin-bottom:1.25rem;">
                <div style="font-size:1.25rem;font-weight:700;color:#e2e8f0;
                            display:flex;align-items:center;gap:0.5rem;">
                    💼 Finance Credit Agent
                </div>
                <div style="font-size:0.78rem;color:#475569;margin-top:0.3rem;line-height:1.5;">
                    Enterprise-grade AI workflow for automated<br>overdue invoice follow-ups.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Workflow steps
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:700;color:#475569;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">'
            "Workflow Steps</div>",
            unsafe_allow_html=True,
        )

        steps = [
            "Enter invoice details",
            "Agent calculates overdue days",
            "Determines follow-up stage & tone",
            "Generates personalised email draft",
            "Automated validation",
            "Human approval (interrupt)",
            "Approved → Audit logging",
            "Rejected → Feedback & regenerate",
            "Max retries → Escalation",
        ]
        steps_html = ""
        for i, step in enumerate(steps, 1):
            steps_html += (
                f'<div class="workflow-step">'
                f'<div class="step-num">{i}</div>'
                f'<div>{step}</div></div>'
            )
        st.markdown(steps_html, unsafe_allow_html=True)

        st.markdown("---")

        # Session state panel
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:700;color:#475569;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">'
            "Session Info</div>",
            unsafe_allow_html=True,
        )

        thread_id = st.session_state.get("thread_id") or "—"
        retry_count = "—"
        validation_status = "—"
        workflow_phase = "Idle"

        output = st.session_state.get("output_state")
        if output:
            retry_count = str(output.get("retry_count", "—"))
            validation_status = str(output.get("validation_status", "—"))

        if st.session_state.get("workflow_completed"):
            workflow_phase = "✅ Completed"
        elif st.session_state.get("interrupt_payload"):
            workflow_phase = "⏸ Awaiting Approval"
        elif st.session_state.get("output_state"):
            workflow_phase = "🔄 In Progress"

        rows = [
            ("Thread ID", thread_id[:22] + "…" if len(thread_id) > 22 else thread_id),
            ("Retry Count", retry_count),
            ("Validation", validation_status),
            ("Phase", workflow_phase),
        ]
        rows_html = ""
        for label, value in rows:
            rows_html += (
                f'<div class="sidebar-info-row">'
                f'<span class="sidebar-info-label">{label}</span>'
                f'<span class="sidebar-info-value">{value}</span>'
                f'</div>'
            )
        st.markdown(rows_html, unsafe_allow_html=True)

        st.markdown("---")

        # Quick reset button in sidebar
        if st.button("🔄 Reset Session", use_container_width=True, key="sidebar_reset"):
            reset_session()
            st.rerun()

        st.markdown(
            '<div style="font-size:0.7rem;color:#334155;text-align:center;'
            'margin-top:2rem;">Powered by LangGraph + Claude</div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: MAIN PAGE HEADER
# ──────────────────────────────────────────────────────────────────────────────

def render_header() -> None:
    """Render the top hero section with title, subtitle, and feature tags."""
    st.markdown(
        '<div class="hero-title">Finance Credit Follow-Up AI Agent</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-sub">Enterprise-grade AI workflow for automated overdue invoice follow-ups</div>',
        unsafe_allow_html=True,
    )

    features = [
        "🤖 Personalised Email Generation",
        "✅ Automated Validation",
        "👤 Human-in-the-Loop Approval",
        "📝 Audit Logging",
        "🚨 Escalation Handling",
        "🔁 Retry Management",
    ]
    tags_html = '<div class="feature-tags">' + "".join(
        f'<span class="feature-tag">{f}</span>' for f in features
    ) + "</div>"
    st.markdown(tags_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: INVOICE INPUT FORM
# ──────────────────────────────────────────────────────────────────────────────

def render_invoice_form() -> None:
    """Render the invoice input form and handle Run Agent / Reset actions."""
    st.markdown(
        '<div class="section-header">📄 Invoice Details</div>',
        unsafe_allow_html=True,
    )

    with st.form(key="invoice_form", clear_on_submit=False):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            invoice_no = st.text_input(
                "Invoice Number",
                value="INV-2026-101",
                placeholder="e.g. INV-2026-001",
                help="Unique invoice identifier",
            )
            client = st.text_input(
                "Client Name",
                value="ABC Technologies Pvt Ltd",
                placeholder="e.g. Acme Corp",
                help="Full legal name of the client",
            )
            contact_email = st.text_input(
                "Contact Email",
                value="finance@abctech.com",
                placeholder="e.g. accounts@client.com",
                help="Finance contact email address",
            )

        with col2:
            amount = st.number_input(
                "Amount Due (₹)",
                value=45250.75,
                min_value=0.01,
                format="%.2f",
                help="Outstanding invoice amount",
            )
            due_date = st.text_input(
                "Due Date",
                value="1 May 2026",
                placeholder="e.g. 15 April 2026",
                help="Invoice due date in human-readable format",
            )

        with col3:
            followup_count = st.number_input(
                "Follow-Up #",
                value=1,
                min_value=0,
                max_value=10,
                step=1,
                help="Number of previous follow-ups sent",
            )
            max_retries = st.number_input(
                "Max Retries",
                value=3,
                min_value=1,
                max_value=10,
                step=1,
                help="Maximum email regeneration attempts on rejection",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        btn_col1, btn_col2, _ = st.columns([1.5, 1, 4])
        with btn_col1:
            submitted = st.form_submit_button(
                "🚀 Run Agent",
                type="primary",
                use_container_width=True,
            )
        with btn_col2:
            reset_clicked = st.form_submit_button(
                "🔄 Reset",
                type="secondary",
                use_container_width=True,
            )

    # ── Handle Reset ──────────────────────────────────────────────────
    if reset_clicked:
        reset_session()
        st.rerun()

    # ── Handle Run Agent ──────────────────────────────────────────────
    if submitted:
        if not invoice_no.strip():
            st.error("Invoice number is required.")
            return
        if not client.strip():
            st.error("Client name is required.")
            return
        if not contact_email.strip():
            st.error("Contact email is required.")
            return

        thread_id = f"invoice-{invoice_no.strip()}"
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = build_initial_state(
            invoice_no, client, amount, due_date,
            contact_email, followup_count, max_retries,
        )

        st.session_state["thread_id"] = thread_id
        st.session_state["config"] = config
        st.session_state["initial_state"] = initial_state
        st.session_state["workflow_completed"] = False
        st.session_state["interrupt_payload"] = None
        st.session_state["output_state"] = None
        st.session_state["current_email_preview"] = None

        with st.spinner("🤖 Running AI agent workflow…"):
            try:
                output_state = run_agent(initial_state, config)
                st.session_state["output_state"] = output_state

                if "__interrupt__" in output_state:
                    payload = output_state["__interrupt__"][0].value
                    st.session_state["interrupt_payload"] = payload
                    st.session_state["current_email_preview"] = payload.get(
                        "email_preview", {}
                    )
                else:
                    st.session_state["workflow_completed"] = True

            except Exception as exc:
                st.exception(exc)

        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: EMAIL PREVIEW CARD
# ──────────────────────────────────────────────────────────────────────────────

def render_email_preview(email_preview: dict) -> None:
    """Render the generated email draft in a styled card."""
    if not email_preview:
        st.info("No email preview available.")
        return

    recipient = email_preview.get("recipient", "—")
    subject = email_preview.get("subject", "—")
    tone = email_preview.get("tone", "—")
    body = email_preview.get("body", "")

    tone_html = _tone_badge_html(tone)

    meta_html = f"""
    <div class="email-card">
        <div class="email-meta-row">
            <span class="email-meta-label">To</span>
            <span class="email-meta-value">{recipient}</span>
        </div>
        <div class="email-meta-row">
            <span class="email-meta-label">Subject</span>
            <span class="email-meta-value">{subject}</span>
        </div>
        <div class="email-meta-row">
            <span class="email-meta-label">Tone</span>
            <span>{tone_html}</span>
        </div>
        <hr class="email-divider"/>
        <div class="email-body">{body}</div>
    </div>
    """
    st.markdown(meta_html, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: WORKFLOW ACTION CARD (helper)
# ──────────────────────────────────────────────────────────────────────────────

def render_workflow_action(state: dict) -> None:
    """
    Inspect workflow state and display the appropriate action banner.

    Priority order:
      1. days_overdue == 0  →  No-overdue informational card
      2. escalation_required == True  →  Escalation alert card
      3. send_status == "sent"  →  Email sent success card
    """
    days_overdue        = state.get("days_overdue", None)
    escalation_required = state.get("escalation_required", False)
    send_status         = state.get("send_status", "")
    send_error          = state.get("send_error", "")

    # ── 1. Invoice not overdue ────────────────────────────────────────
    if days_overdue == 0:
        st.markdown(
            """
            <div class="card card-accent action-banner">
                <div class="action-banner-title" style="color:#60a5fa;">
                    ℹ️ Invoice Is Not Overdue
                </div>
                <div class="action-banner-body" style="color:#94a3b8;">
                    No follow-up email was generated or sent because the invoice
                    due date has not passed.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── 2. Escalation sent ────────────────────────────────────────────
    if escalation_required:
        reason = send_error or "Escalated for manager review."
        st.markdown(
            f"""
            <div class="card card-danger action-banner">
                <div class="action-banner-title" style="color:#f87171;">
                    🚨 Escalation Notification Sent to Finance Manager
                </div>
                <div class="action-banner-body" style="color:#fca5a5;">
                    The overdue invoice has been escalated for manual review.
                </div>
                <div class="action-banner-detail-row" style="color:#fca5a5;">
                    <span class="action-banner-detail-label">Manager Contact:</span>
                    <span class="action-banner-detail-value">finance.manager@company.com</span>
                </div>
                <div class="action-banner-detail-row" style="color:#fca5a5;">
                    <span class="action-banner-detail-label">Reason:</span>
                    <span class="action-banner-detail-value">{reason}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── 3. Email sent successfully ────────────────────────────────────
    if send_status == "sent":
        email_draft = state.get("email_draft")
        detail_rows = ""

        if email_draft:
            if hasattr(email_draft, "__dict__"):
                recipient = getattr(email_draft, "recipient", None)
                subject   = getattr(email_draft, "subject", None)
                tone      = getattr(email_draft, "tone", None)
            elif isinstance(email_draft, dict):
                recipient = email_draft.get("recipient")
                subject   = email_draft.get("subject")
                tone      = email_draft.get("tone")
            else:
                recipient = subject = tone = None

            if recipient:
                detail_rows += (
                    f'<div class="action-banner-detail-row" style="color:#6ee7b7;">'
                    f'<span class="action-banner-detail-label">Recipient:</span>'
                    f'<span class="action-banner-detail-value">{recipient}</span>'
                    f'</div>'
                )
            if subject:
                detail_rows += (
                    f'<div class="action-banner-detail-row" style="color:#6ee7b7;">'
                    f'<span class="action-banner-detail-label">Subject:</span>'
                    f'<span class="action-banner-detail-value">{subject}</span>'
                    f'</div>'
                )
            if tone:
                tone_badge = _tone_badge_html(tone)
                detail_rows += (
                    f'<div class="action-banner-detail-row" style="color:#6ee7b7;">'
                    f'<span class="action-banner-detail-label">Tone:</span>'
                    f'<span>{tone_badge}</span>'
                    f'</div>'
                )

        st.markdown(
            f"""
            <div class="card card-success action-banner">
                <div class="action-banner-title" style="color:#34d399;">
                    📧 Payment Follow-Up Email Sent Successfully
                </div>
                <div class="action-banner-body" style="color:#6ee7b7;">
                    Recipient email has been processed and the follow-up
                    communication has been completed.
                </div>
                {detail_rows}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: WORKFLOW STATUS PANEL
# ──────────────────────────────────────────────────────────────────────────────

def render_workflow_status(state: dict) -> None:
    """Render key workflow metrics, status indicators, and action banners."""
    st.markdown(
        '<div class="section-header">📊 Workflow Status</div>',
        unsafe_allow_html=True,
    )

    days_overdue      = state.get("days_overdue", "—")
    stage_key         = state.get("stage_key", "—")
    validation_status = state.get("validation_status", "—")
    retry_count       = state.get("retry_count", 0)
    send_status       = state.get("send_status", "—")
    send_error        = state.get("send_error", None)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📅 Days Overdue", days_overdue)
    with col2:
        st.metric("🎯 Stage", stage_key)
    with col3:
        st.metric("🔁 Retry Count", retry_count)
    with col4:
        st.metric("📤 Send Status", send_status)

    # Validation status coloured indicator
    if validation_status and validation_status != "—":
        vs_lower = str(validation_status).lower()
        if "pass" in vs_lower or "valid" in vs_lower or vs_lower == "true":
            st.markdown(
                f'<div class="card card-success" style="margin-top:0.75rem;font-size:0.88rem;">'
                f'✅ &nbsp;<strong>Validation:</strong> &nbsp;'
                f'{_pill_html(str(validation_status), "green")}</div>',
                unsafe_allow_html=True,
            )
        elif "fail" in vs_lower or "invalid" in vs_lower or vs_lower == "false":
            st.markdown(
                f'<div class="card card-danger" style="margin-top:0.75rem;font-size:0.88rem;">'
                f'❌ &nbsp;<strong>Validation:</strong> &nbsp;'
                f'{_pill_html(str(validation_status), "red")}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="card card-accent" style="margin-top:0.75rem;font-size:0.88rem;">'
                f'ℹ️ &nbsp;<strong>Validation:</strong> &nbsp;'
                f'{_pill_html(str(validation_status), "blue")}</div>',
                unsafe_allow_html=True,
            )

    if send_error:
        st.markdown(
            f'<div class="card card-danger" style="margin-top:0.5rem;font-size:0.85rem;">'
            f'⚠️ <strong>Send Error:</strong> {send_error}</div>',
            unsafe_allow_html=True,
        )

    # ── Workflow action banner (below metrics) ────────────────────────
    render_workflow_action(state)


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: AUDIT LOG
# ──────────────────────────────────────────────────────────────────────────────

def render_audit_log(audit_log: dict) -> None:
    """Render the audit log in a collapsible formatted viewer."""
    if not audit_log:
        return

    st.markdown(
        '<div class="section-header">📝 Audit Log</div>',
        unsafe_allow_html=True,
    )

    with st.expander("📋 View Full Audit Log", expanded=False):
        # Human-friendly table view
        col_a, col_b = st.columns([1, 2])
        with col_a:
            for key in audit_log:
                st.markdown(
                    f'<div style="font-size:0.82rem;color:#475569;font-weight:600;'
                    f'padding:0.35rem 0;border-bottom:1px solid #1e2a3a;">{key}</div>',
                    unsafe_allow_html=True,
                )
        with col_b:
            for value in audit_log.values():
                st.markdown(
                    f'<div style="font-size:0.82rem;color:#e2e8f0;'
                    f'padding:0.35rem 0;border-bottom:1px solid #1e2a3a;'
                    f'font-family: DM Mono, monospace;">{value}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.75rem;color:#475569;margin-bottom:0.4rem;">'
            "Raw JSON</div>",
            unsafe_allow_html=True,
        )
        st.json(audit_log)


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: HUMAN APPROVAL (INTERRUPT HANDLER)
# ──────────────────────────────────────────────────────────────────────────────

def handle_interrupt() -> None:
    """
    Display the interrupt approval UI. On Approve/Reject the workflow is
    resumed and session state is updated accordingly.
    """
    payload = st.session_state.get("interrupt_payload")
    if not payload:
        return

    config = st.session_state["config"]
    email_preview = st.session_state.get("current_email_preview", {})

    # ── Approval required banner ──────────────────────────────────────
    st.markdown(
        """
        <div class="card card-warning"
             style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem;">
            <span style="font-size:1.4rem;">⏸</span>
            <div>
                <div style="font-size:1rem;font-weight:700;color:#fbbf24;">
                    Human Approval Required
                </div>
                <div style="font-size:0.85rem;color:#92400e;margin-top:0.2rem;">
                    The agent has generated an email draft and is awaiting your decision.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    title   = payload.get("title", "Approval Required")
    message = payload.get("message", "")

    if title:
        st.markdown(
            f'<div style="font-size:1rem;font-weight:600;color:#e2e8f0;'
            f'margin:0.75rem 0 0.25rem;">{title}</div>',
            unsafe_allow_html=True,
        )
    if message:
        st.markdown(
            f'<div style="font-size:0.88rem;color:#94a3b8;margin-bottom:1rem;">'
            f'{message}</div>',
            unsafe_allow_html=True,
        )

    # ── Email preview ─────────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">✉️ Generated Email Draft</div>',
        unsafe_allow_html=True,
    )
    render_email_preview(email_preview)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Approval action buttons ───────────────────────────────────────
    st.markdown(
        '<div class="section-header">👤 Your Decision</div>',
        unsafe_allow_html=True,
    )

    btn_col1, btn_col2, _ = st.columns([1, 1, 4])

    with btn_col1:
        approve_clicked = st.button(
            "✅ Approve",
            type="primary",
            use_container_width=True,
            key="approve_btn",
        )
    with btn_col2:
        reject_clicked = st.button(
            "❌ Reject",
            type="secondary",
            use_container_width=True,
            key="reject_btn",
        )

    # ── Reject feedback area ──────────────────────────────────────────
    feedback_text = ""
    if reject_clicked:
        st.session_state["_show_feedback"] = True

    if st.session_state.get("_show_feedback"):
        feedback_text = st.text_area(
            "📝 Rejection Feedback",
            placeholder=(
                "Describe what needs improvement, e.g.:\n"
                "• Make the tone more polite.\n"
                "• Mention the invoice amount more clearly.\n"
                "• Shorten the subject line."
            ),
            height=120,
            key="feedback_area",
        )

        submit_reject = st.button(
            "Submit Rejection",
            type="primary",
            key="submit_reject_btn",
        )

        if submit_reject:
            if not feedback_text.strip():
                st.warning("⚠️ Please provide feedback before rejecting.")
                return

            with st.spinner("🔄 Sending rejection feedback to agent…"):
                try:
                    new_output = resume_agent("reject", feedback_text.strip(), config)
                    st.session_state["output_state"] = new_output
                    st.session_state["_show_feedback"] = False

                    if "__interrupt__" in new_output:
                        new_payload = new_output["__interrupt__"][0].value
                        st.session_state["interrupt_payload"] = new_payload
                        st.session_state["current_email_preview"] = new_payload.get(
                            "email_preview", {}
                        )
                    else:
                        st.session_state["interrupt_payload"] = None
                        st.session_state["workflow_completed"] = True

                except Exception as exc:
                    st.exception(exc)

            st.rerun()

    # ── Handle Approve ────────────────────────────────────────────────
    if approve_clicked:
        with st.spinner("✅ Approving and finalising workflow…"):
            try:
                new_output = resume_agent("approve", "", config)
                st.session_state["output_state"] = new_output
                st.session_state["interrupt_payload"] = None
                st.session_state["_show_feedback"] = False

                if "__interrupt__" in new_output:
                    # Unexpected second interrupt
                    new_payload = new_output["__interrupt__"][0].value
                    st.session_state["interrupt_payload"] = new_payload
                    st.session_state["current_email_preview"] = new_payload.get(
                        "email_preview", {}
                    )
                else:
                    st.session_state["workflow_completed"] = True

            except Exception as exc:
                st.exception(exc)

        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: FINAL APPROVED EMAIL
# ──────────────────────────────────────────────────────────────────────────────

def render_final_email(state: dict) -> None:
    """Render the final approved email from the completed workflow state."""
    email_draft = state.get("email_draft")
    if not email_draft:
        return

    st.markdown(
        '<div class="section-header">✉️ Final Approved Email</div>',
        unsafe_allow_html=True,
    )

    # email_draft may be a Pydantic model or a dict
    if hasattr(email_draft, "__dict__"):
        preview = {
            "recipient": getattr(email_draft, "recipient", "—"),
            "subject": getattr(email_draft, "subject", "—"),
            "tone": getattr(email_draft, "tone", "—"),
            "body": getattr(email_draft, "body", ""),
        }
    elif isinstance(email_draft, dict):
        preview = email_draft
    else:
        st.info("Email draft format unrecognised.")
        return

    render_email_preview(preview)


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: FINAL SUMMARY BANNER
# ──────────────────────────────────────────────────────────────────────────────

def render_final_summary(state: dict) -> None:
    """Render the final workflow outcome with context-aware messaging."""

    st.markdown(
        '<div class="section-header">✅ Workflow Complete</div>',
        unsafe_allow_html=True,
    )

    days_overdue = state.get("days_overdue", 0)
    send_status  = state.get("send_status", "—")
    retry_count  = state.get("retry_count", 0)
    escalated    = state.get("escalation_required", False)

    # Determine workflow outcome
    if days_overdue == 0:
        status_type = "no_overdue"
    elif escalated:
        status_type = "escalated"
    else:
        status_type = "completed"

    # ── Business-oriented summary message ────────────────────────────
    if status_type == "no_overdue":
        st.info(
            "ℹ️ **No Action Required — Invoice Not Overdue**\n\n"
            "This invoice is not overdue, so no payment follow-up email "
            "was generated or sent."
        )

    elif status_type == "escalated":
        st.error(
            "🚨 **Escalation Notification Sent to Finance Manager**\n\n"
            "The overdue invoice could not be resolved through automated follow-ups "
            "and has been escalated to the finance manager for manual review and "
            "intervention.\n\n"
            f"Retries used: **{retry_count}**"
        )

    else:
        st.success(
            "🎉 **Payment Follow-Up Email Sent Successfully**\n\n"
            "The payment follow-up email was generated, approved by the human reviewer, "
            "and delivered successfully to the client.\n\n"
            f"Send status: **{send_status}**  \n"
            f"Retries used: **{retry_count}**"
        )

    # ── Workflow action card (detailed banner) ────────────────────────
    render_workflow_action(state)

    # ── Summary metrics ───────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📤 Send Status", send_status)

    with col2:
        st.metric("🔁 Retries Used", retry_count)

    with col3:
        st.metric("🚨 Escalated", "Yes" if escalated else "No")

    with col4:
        st.metric("🕐 Completed At", datetime.now().strftime("%H:%M:%S"))


# ──────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION ENTRYPOINT
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Main Streamlit application controller."""

    render_sidebar()
    render_header()

    # ── Invoice input form (always visible until workflow runs) ───────
    if not st.session_state.get("output_state"):
        render_invoice_form()
        return

    # ── From here: workflow has been invoked at least once ────────────
    output_state = st.session_state["output_state"]

    # ── Workflow status panel (always shown once running) ─────────────
    render_workflow_status(output_state)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Interrupt handling (human approval loop) ──────────────────────
    if st.session_state.get("interrupt_payload"):
        handle_interrupt()

    # ── Completed workflow sections ───────────────────────────────────
    elif st.session_state.get("workflow_completed"):
        render_final_summary(output_state)
        st.markdown("<br>", unsafe_allow_html=True)
        render_final_email(output_state)
        st.markdown("<br>", unsafe_allow_html=True)
        render_audit_log(output_state.get("audit_log", {}))

        # Allow user to start a new run
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "🆕 Process Another Invoice",
            type="primary",
            key="new_invoice_btn",
        ):
            reset_session()
            st.rerun()

    else:
        # Intermediate state — workflow ran but no interrupt and not complete
        st.info(
            "ℹ️ Workflow is in progress. "
            "If you see this message unexpectedly, check your agent configuration."
        )
        if st.button("🔄 Reset", key="mid_reset_btn"):
            reset_session()
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()