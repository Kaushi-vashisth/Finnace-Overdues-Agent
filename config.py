from models import StageKey,StageMeta

stage_values: dict[StageKey, StageMeta] = {
    "1st Follow-Up": {
        "followup_number": 1,
        "tone": "Warm & Friendly",
        "key_message": "This appears to be a friendly reminder in case the invoice was overlooked.",
        "cta": "Please complete the payment at your earliest convenience.",
        "escalation_required": False,
    },
    "2nd Follow-Up": {
        "followup_number": 2,
        "tone": "Polite but Firm",
        "key_message": "The payment is still pending and we would appreciate an update.",
        "cta": "Please confirm your expected payment date.",
        "escalation_required": False,
    },
    "3rd Follow-Up": {
        "followup_number": 3,
        "tone": "Formal & Serious",
        "key_message": "The invoice remains unpaid and requires immediate attention.",
        "cta": "Please respond within 48 hours.",
        "escalation_required": False,
    },
    "4th Follow-Up": {
        "followup_number": 4,
        "tone": "Stern & Urgent",
        "key_message": "This is a final reminder before escalation.",
        "cta": "Please make payment immediately or contact us.",
        "escalation_required": False,
    },
    "Escalation Flag": {
        "followup_number": 5,
        "tone": "Legal Review Required",
        "key_message": "The case requires human review.",
        "cta": "Assign to finance manager.",
        "escalation_required": True,
    },
}