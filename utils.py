from models import InvoiceData

def generate_payment_link(invoice_no: str) -> str:
    return f"https://pay.company.com/{invoice_no}"

def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return ""

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[:2] + "*" * (len(local) - 2)

    return f"{masked_local}@{domain}"

def build_subject(
    template: str,
    invoice: InvoiceData,
    days_overdue: int,
) -> str:
    formatted_amount = f"{invoice['amount']:,.0f}"

    return template.format(
        invoice_no=invoice["invoice_no"],
        amount=formatted_amount,
        days_overdue=days_overdue,
    )