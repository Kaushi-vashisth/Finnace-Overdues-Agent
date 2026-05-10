from workflow import agent
from models import InvoiceData, AgentState
from pprint import pprint
from langgraph.types import Command

def print_separator(title: str = ""):
    print("\n" + "=" * 100)
    if title:
        print(title.center(100))
        print("=" * 100)


def print_email_preview(email_preview: dict):
    print_separator("GENERATED EMAIL DRAFT")

    print(f"To      : {email_preview.get('recipient', '')}")
    print(f"Subject : {email_preview.get('subject', '')}")
    print(f"Tone    : {email_preview.get('tone', '')}")

    print("\n" + "-" * 100)
    print("BODY")
    print("-" * 100)
    print(email_preview.get("body", ""))
    print("-" * 100)


def print_audit_log(audit_log: dict):
    print_separator("AUDIT LOG")

    for key, value in audit_log.items():
        print(f"{key:25}: {value}")


def print_final_summary(state: AgentState):
    print_separator("WORKFLOW SUMMARY")

    summary_fields = [
        "days_overdue",
        "stage_key",
        "validation_status",
        "retry_count",
        "send_status",
        "send_error",
    ]

    for field in summary_fields:
        if field in state:
            print(f"{field:25}: {state[field]}")

    if state.get("email_draft"):
        email = state["email_draft"]

        print_separator("FINAL APPROVED EMAIL")

        print(f"Recipient : {email.recipient}")
        print(f"Subject   : {email.subject}")
        print(f"Tone      : {email.tone}")

        print("\nBody:\n")
        print(email.body)

    if state.get("audit_log"):
        print_audit_log(state["audit_log"])


def get_user_decision() -> tuple[str, str]:
    while True:
        decision = input(
            "\nApprove or Reject this email? (approve/reject): "
        ).strip().lower()

        if decision in {"approve", "reject"}:
            break

        print("Please enter either 'approve' or 'reject'.")

    feedback = ""

    if decision == "reject":
        print("\nProvide feedback to improve the email.")
        print("Examples:")
        print("- Make the tone more polite.")
        print("- Mention the amount more clearly.")
        print("- Shorten the subject line.")

        feedback = input("\nFeedback: ").strip()

        if not feedback:
            feedback = "User requested changes to the email draft."

    return decision, feedback


def run_workflow(initial_state: AgentState):
    thread_id = f"invoice-{initial_state['invoice']['invoice_no']}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    print_separator("STARTING FINANCE FOLLOW-UP AGENT")

    print("Invoice Details:")
    pprint(initial_state["invoice"])

    # Initial invocation
    output_state = agent.invoke(initial_state, config=config)

    # Handle all human approval interrupts
    while "__interrupt__" in output_state:
        interrupt_payload = output_state["__interrupt__"][0].value

        print_separator(interrupt_payload.get("title", "APPROVAL REQUIRED"))
        print(interrupt_payload.get("message", ""))

        email_preview = interrupt_payload.get("email_preview", {})
        if email_preview:
            print_email_preview(email_preview)

        decision, feedback = get_user_decision()

        print_separator("RESUMING WORKFLOW")
        print(f"Decision : {decision}")
        if feedback:
            print(f"Feedback : {feedback}")

        output_state = agent.invoke(
            Command(
                resume={
                    "decision": decision,
                    "feedback": feedback,
                }
            ),
            config=config,
        )

    print_final_summary(output_state)

    return output_state


if __name__ == "__main__":
    invoice: InvoiceData = {
        "invoice_no": "INV-2026-101",
        "client": "ABC Technologies Pvt Ltd",
        "amount": 45250.75,
        "due_date": "11 May 2026",
        "contact_email": "finance@abctech.com",
        "followup_count": 1,
    }

    initial_state: AgentState = {
        "invoice": invoice,
        "retry_count": 0,
        "max_retries": 3,
    }

    final_state = run_workflow(initial_state)