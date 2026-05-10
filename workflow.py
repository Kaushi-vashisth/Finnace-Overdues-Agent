from typing import Literal
from datetime import datetime,timezone
from dateutil.parser import parse
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from models import *
from prompts import *
from config import *
from utils import *

# =========================================================
# NODES
# =========================================================

def get_overdue_days(state: AgentState) -> AgentState:
    due_date = state["invoice"]["due_date"]
    parsed = parse(str(due_date), dayfirst=True).date()
    today = datetime.today().date()
    days_overdue = max((today - parsed).days, 0)
    return {**state, "days_overdue": days_overdue}


def set_stage(state: AgentState) -> AgentState:
    days = state["days_overdue"]

    if days == 0:
        return {
            **state,
            "stage_key": None,
            "stage_meta": None,
            "escalation_required": False,
        }
    
    if 1 <= days <= 7:
        stage = "1st Follow-Up"
    elif 8 <= days <= 14:
        stage = "2nd Follow-Up"
    elif 15 <= days <= 21:
        stage = "3rd Follow-Up"
    elif 22 <= days <= 30:
        stage = "4th Follow-Up"
    else:
        stage = "Escalation Flag"

    return {
        **state,
        "stage_key": stage,
        "stage_meta": stage_values[stage],
        "escalation_required": stage_values[stage]["escalation_required"],
    }


def check_overdue(state: AgentState) -> Literal["escalation", "generate_email_draft","no_overdue"]:
    if state["days_overdue"] == 0:
        return "no_overdue"
    elif state["days_overdue"] > 30:
        return "escalation"
    return "generate_email_draft"


def generate_email_draft(state: AgentState) -> AgentState:
    invoice = state["invoice"]
    stage_meta = state["stage_meta"]

    payment_link = state.get("payment_link")
    if not payment_link:
        payment_link = generate_payment_link(invoice["invoice_no"])

    subject = build_subject(
        stage_meta["subject_template"],
        invoice,
        state["days_overdue"],
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", System_prompt),
            ("human", Human_prompt),
        ]
    )

    email_generation_chain = prompt | email_agent

    details = {
        "client_name": invoice["client"],
        "recipient_email": invoice["contact_email"],
        "invoice_id": invoice["invoice_no"],
        "amount": invoice["amount"],
        "due_date": invoice["due_date"],
        "days_overdue": state["days_overdue"],
        "stage": state["stage_key"],
        "tone": stage_meta["tone"],
        "key_message": stage_meta["key_message"],
        "cta": stage_meta["cta"],
        "payment_link": payment_link,
        "finance_contact": "finance@company.com",
        "validation_feedback": state.get("validation_feedback", "None"),
        "subject": subject
    }

    email_draft = email_generation_chain.invoke(details)

    return {
        **state,
        "payment_link": payment_link,
        "email_draft": email_draft,
    }


def validate_draft_email(state: AgentState) -> AgentState:
    validation_status = "approved"
    validation_feedback = ""

    stage_meta = state["stage_meta"]
    email_draft = state.get("email_draft")
    invoice = state["invoice"]

    retry_count = state.get("retry_count", 0)

    if not email_draft:
        validation_status = "rejected"
        validation_feedback = "No email draft generated."

    elif (
        str(email_draft.recipient).strip().lower()
        != invoice["contact_email"].strip().lower()
    ):
        validation_status = "rejected"
        validation_feedback = "Recipient email does not match invoice contact email."

    elif email_draft.tone.strip() != stage_meta["tone"].strip():
        validation_status = "rejected"
        validation_feedback = f"Tone must be exactly '{stage_meta['tone']}'."

    else:
        # Validate exact subject match against deterministic template
        expected_subject = build_subject(
            stage_meta["subject_template"],
            invoice,
            state["days_overdue"],
        )

        if email_draft.subject.strip() != expected_subject.strip():
            validation_status = "rejected"
            validation_feedback = (
                f"Subject must be exactly: '{expected_subject}'"
            )

        else:
            # Validate required content in the body
            full_email_text = " ".join([
                email_draft.greeting,
                email_draft.body,
                email_draft.closing,
            ])

            required_values = [
                invoice["client"],
                invoice["invoice_no"],
                str(invoice["due_date"]),
                str(state["days_overdue"]),
                state["payment_link"],
            ]

            for value in required_values:
                if str(value) not in full_email_text:
                    validation_status = "rejected"
                    validation_feedback = f"Email must include: {value}"
                    break

            if validation_status == "rejected":
                retry_count += 1

    if validation_status == "approved":
        user_decision = interrupt(
            {
                "type": "approval_request",
                "title": "Review Generated Payment Follow-Up Email",
                "message": "Approve or reject the generated email.",
                "email_preview": {
                    "recipient": str(email_draft.recipient),
                    "subject": email_draft.subject,
                    "greeting": email_draft.greeting,
                    "body": email_draft.body,
                    "closing": email_draft.closing,
                    "tone": email_draft.tone,
                },
            }
        )

        if user_decision["decision"] == "reject":
            validation_status = "rejected"
            validation_feedback = user_decision.get(
                "feedback",
                "User requested changes to the email draft."
            )
            retry_count += 1

    return {
        **state,
        "validation_status": validation_status,
        "validation_feedback": validation_feedback,
        "retry_count": retry_count,
    }


def check_validation(
    state: AgentState,
) -> Literal["send_email", "generate_email_draft", "escalation"]:
    if state["validation_status"] == "approved":
        return "send_email"

    if state["retry_count"] >= state["max_retries"]:
        return "escalation"

    return "generate_email_draft"

def no_overdue_node(state: AgentState) -> AgentState:
    """
    Handles invoices that are not overdue.
    No email is generated or sent.
    """
    invoice = state["invoice"]

    return {
        **state,
        "validation_status": "approved",
        "validation_feedback": "Invoice is not overdue.",
        "send_status": "not_sent",
        "send_error": "Invoice is not overdue.",
        "escalation_required": False,
        "audit_log": {
            "status": "no_action_required",
            "message": (
                f"Invoice {invoice['invoice_no']} for "
                f"{invoice['client']} is not overdue. "
                "No follow-up email was generated."
            ),
        },
    }

def send_email_node(state: AgentState) -> AgentState:
    """
    Dummy email sender.
    Simulates sending the generated email to the customer.
    """
    email_draft = state.get("email_draft")

    if not email_draft:
        return {
            **state,
            "send_status": "failed",
            "send_error": "No email draft available to send.",
        }

    print("\n" + "=" * 80)
    print("SENDING PAYMENT FOLLOW-UP EMAIL")
    print("=" * 80)
    print(f"To      : {email_draft.recipient}")
    print(f"Subject : {email_draft.subject}")
    print(f"Tone    : {email_draft.tone}")
    print("=" * 80)

    return {
        **state,
        "send_status": "sent",
        "send_error": "",
    }


def escalation_node(state: AgentState) -> AgentState:
    """
    Dummy escalation handler.
    Simulates sending an escalation notification to the finance manager.
    """
    invoice = state["invoice"]
    manager_email = "finance.manager@company.com"

    subject = f"Escalation Required: Invoice {invoice['invoice_no']}"
    body = (
        f"Invoice {invoice['invoice_no']} for client {invoice['client']} "
        f"is {state['days_overdue']} days overdue and requires manual review."
    )

    print("\n" + "=" * 80)
    print("SENDING ESCALATION EMAIL TO MANAGER")
    print("=" * 80)
    print(f"To      : {manager_email}")
    print(f"Subject : {subject}")
    print("\nBody:")
    print(body)
    print("=" * 80)

    return {
        **state,
        "send_status": "not_sent",
        "send_error": "Escalated for manager review.",
        "escalation_required": True,
    }


def auditLog(state: AgentState) -> AgentState:
    invoice = state["invoice"]
    stage_meta = state.get("stage_meta")
    email_draft = state.get("email_draft")

    audit_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),

        # Invoice details
        "invoice_no": invoice["invoice_no"],
        "client": invoice["client"],
        "amount": invoice["amount"],
        "due_date": invoice["due_date"],
        "contact_email": mask_email(invoice["contact_email"]),
        "followup_count": invoice["followup_count"],

        # Workflow details
        "days_overdue": state.get("days_overdue"),
        "stage_key": state.get("stage_key"),
        "escalation_required": state.get("escalation_required", False),

        # Stage metadata
        "followup_number": (
            stage_meta["followup_number"] if stage_meta else None
        ),
        "key_message": (
            stage_meta["key_message"] if stage_meta else None
        ),
        "cta": (
            stage_meta["cta"] if stage_meta else None
        ),

        # Payment details
        "payment_link": state.get("payment_link", ""),

        # Email details
        "recipient": (
            mask_email(str(email_draft.recipient))
            if email_draft else ""
        ),
        "subject": (
            email_draft.subject if email_draft else ""
        ),
        "tone_used": (
            email_draft.tone
            if email_draft
            else (stage_meta["tone"] if stage_meta else "")
        ),

        # Validation
        "validation_status": state.get("validation_status"),
        "validation_feedback": state.get("validation_feedback", ""),

        # Sending
        "send_status": state.get("send_status", "not_sent"),
        "send_error": state.get("send_error", ""),

        # Retry info
        "retry_count": state.get("retry_count", 0),
        "max_retries": state.get("max_retries", 0),
    }

    return {
        **state,
        "audit_log": audit_log,
    }


# =========================================================
# GRAPH
# =========================================================

checkpointer = MemorySaver()
graph = StateGraph(AgentState)

# =========================================================
# NODES
# =========================================================

graph.add_node("get_overdue_days", get_overdue_days)
graph.add_node("set_stage", set_stage)
graph.add_node("no_overdue", no_overdue_node)
graph.add_node("generate_email_draft", generate_email_draft)
graph.add_node("validate_draft_email", validate_draft_email)
graph.add_node("send_email", send_email_node)
graph.add_node("escalation", escalation_node)
graph.add_node("auditLog", auditLog)

# =========================================================
# EDGES
# =========================================================

graph.add_edge(START, "get_overdue_days")
graph.add_edge("get_overdue_days", "set_stage")

# Routing:
# - days_overdue == 0  -> no_overdue
# - days_overdue > 30  -> escalation
# - otherwise          -> generate_email_draft
graph.add_conditional_edges("set_stage", check_overdue)

# Email generation -> validation
graph.add_edge("generate_email_draft", "validate_draft_email")

# Validation routing:
# - approved                    -> send_email
# - rejected and retries left   -> generate_email_draft
# - rejected and retries over   -> escalation
graph.add_conditional_edges("validate_draft_email",check_validation)

# Successful email send -> audit log
graph.add_edge("send_email", "auditLog")

# Non-overdue invoices -> audit log
graph.add_edge("no_overdue", "auditLog")

# Escalated cases -> audit log
graph.add_edge("escalation", "auditLog")

# Final node
graph.add_edge("auditLog", END)

# Compile
agent = graph.compile(checkpointer=checkpointer)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    invoice: InvoiceData = {
        "invoice_no": "INV-2026-101",
        "client": "ABC Technologies Pvt Ltd",
        "amount": 45250.75,
        "due_date": "1 Jan 2026",
        "contact_email": "finance@abctech.com",
        "followup_count": 1,
    }

    initial_state: AgentState = {
        "invoice": invoice,
        "retry_count": 0,
        "max_retries": 3,
    }

    thread_id = f"invoice-{invoice['invoice_no']}"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    output_state = agent.invoke(initial_state, config=config)

    while "__interrupt__" in output_state:
        payload = output_state["__interrupt__"][0].value

        print("\n" + "=" * 80)
        print(payload["title"])
        print("=" * 80)

        preview = payload["email_preview"]
        print(f"To      : {preview['recipient']}")
        print(f"Subject : {preview['subject']}")
        print(f"Tone    : {preview['tone']}")
        print("\nBody:\n")
        print(preview["body"])

        while True:
            decision = input("\nApprove or Reject? (approve/reject): ").strip().lower()
            if decision in {"approve", "reject"}:
                break

        feedback = ""
        if decision == "reject":
            feedback = input("Enter feedback: ").strip()

        output_state = agent.invoke(
            Command(
                resume={
                    "decision": decision,
                    "feedback": feedback,
                }
            ),
            config=config,
        )

    print("\nFINAL OUTPUT STATE\n")
    for key, value in output_state.items():
        print(f"{key}:")
        print(value)
        print()
