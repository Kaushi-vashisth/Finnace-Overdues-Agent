from typing import TypedDict, Literal, Optional, Any
from pydantic import BaseModel, Field, EmailStr
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv

load_dotenv()

class EmailDraft(BaseModel):
    recipient: EmailStr = Field(description="Recipient email")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body")
    tone: Literal[
        "Warm & Friendly",
        "Polite but Firm",
        "Formal & Serious",
        "Stern & Urgent",
        "Legal Review Required",
    ] = Field(description="Tone used in the email")


class InvoiceData(TypedDict):
    invoice_no: str
    client: str
    amount: float
    due_date: str
    contact_email: str
    followup_count: int


class StageMeta(TypedDict):
    followup_number: int
    tone: Literal[
        "Warm & Friendly",
        "Polite but Firm",
        "Formal & Serious",
        "Stern & Urgent",
        "Legal Review Required",
    ]
    key_message: str
    cta: str
    escalation_required: bool


StageKey = Literal[
    "1st Follow-Up",
    "2nd Follow-Up",
    "3rd Follow-Up",
    "4th Follow-Up",
    "Escalation Flag",
]


class AgentState(TypedDict, total=False):
    invoice: InvoiceData
    days_overdue: int
    stage_key: StageKey
    stage_meta: StageMeta
    payment_link: str
    email_draft: Optional[EmailDraft]
    validation_status: Literal["approved", "rejected"]
    validation_feedback: str
    retry_count: int
    max_retries: int
    escalation_required: bool
    send_status: Literal["pending", "sent", "failed", "not_sent"]
    send_error: str
    audit_log: dict[str, Any]

model = ChatMistralAI(temperature=0.2)
email_agent = model.with_structured_output(EmailDraft)