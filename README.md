# Finance Credit Follow-Up AI Agent

<div align="center">

# 💰 Finance Credit Follow-Up AI Agent

### Enterprise-grade AI workflow for automating overdue invoice follow-ups

Built with **LangGraph**, **Mistral AI**, and **Streamlit**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Workflow-purple)
![Mistral AI](https://img.shields.io/badge/Mistral-AI-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## 🚀 Overview

The **Finance Credit Follow-Up AI Agent** automates the complete accounts receivable follow-up process.

It analyzes overdue invoices, determines the appropriate escalation stage, generates professional payment reminder emails with adaptive tone, validates output, supports human approval, and escalates severely overdue accounts to a finance manager.

This project demonstrates a production-ready **LangGraph workflow** with:

- Structured state management
- Human-in-the-loop review
- Retry with feedback
- Automatic escalation
- Audit logging
- Streamlit dashboard
- CLI interface

---

## ✨ Features

- 📥 Invoice input and overdue calculation
- 🧠 Dynamic follow-up stage selection
- ✍️ Personalized email generation using Mistral AI
- ✅ Automated output validation
- 👨‍💼 Human-in-the-loop approval
- 🔁 Retry with reviewer feedback
- 🚨 Automatic escalation to finance manager
- 📋 Comprehensive audit logging
- 🔐 PII masking in logs
- 💾 LangGraph checkpoint-based recovery
- 🌐 Streamlit dashboard
- 💻 CLI runner

---

## 🏗️ Workflow Architecture

```text
Invoice Input
     │
     ▼
Overdue Calculation
     │
     ▼
Stage Selection
     │
     ▼
Email Generation (LLM)
     │
     ▼
Validation
     │
     ▼
Human Approval
   ┌───────┴────────┐
Approve          Reject
   │                 │
   ▼                 ▼
Send Email      Retry with Feedback
   │
   ▼
Audit Logging
   │
   ▼
If > 30 Days Overdue
   │
   ▼
Manager Escalation
```

---

## 📌 Follow-Up Stages

| Days Overdue | Stage | Tone | Action |
|------------:|------|------|------|
| 1–7 | 1st Follow-Up | Warm & Friendly | Gentle reminder |
| 8–14 | 2nd Follow-Up | Polite but Firm | Request payment date |
| 15–21 | 3rd Follow-Up | Formal & Serious | 48-hour response request |
| 22–30 | 4th Follow-Up | Stern & Urgent | Final notice |
| 31+ | Escalation Flag | Legal Review Required | Send to finance manager |

---

## 📷 Sample Outputs

### 🟢 Stage 1 — Friendly Reminder (2 Days Overdue)

```text
Subject: Quick Reminder – Invoice #INV-2026-101 | ₹45,251 Due
Tone   : Warm & Friendly

Hi ABC Technologies Pvt Ltd Team,

Hope all is well! We wanted to reach out regarding Invoice #INV-2026-101,
which appears to have been overlooked.

Amount Due: ₹45,250.75
Due Date  : 8 May 2026

Payment Link:
https://pay.company.com/INV-2026-101
```

---

### 🟡 Stage 2 — Polite Follow-Up (10 Days Overdue)

```text
Subject: Payment Follow-Up – Invoice #INV-2026-101 (10 Days Overdue)
Tone   : Polite but Firm

Dear ABC Technologies Pvt Ltd Team,

Invoice #INV-2026-101 for ₹45,250.75 was due on 30 April 2026.

This invoice is currently 10 days overdue.
Could you please confirm the expected payment date?

Payment Link:
https://pay.company.com/INV-2026-101
```

---

### 🟠 Stage 3 — Formal Reminder (18 Days Overdue)

```text
Subject: IMPORTANT: Outstanding Payment – Invoice #INV-2026-101 (18 Days Overdue)
Tone   : Formal & Serious

Dear ABC Technologies Pvt Ltd Team,

Invoice #INV-2026-101 remains unpaid and is now 18 days overdue.

Despite previous reminders, we have not received payment or confirmation.

Please respond within 48 hours.

Payment Link:
https://pay.company.com/INV-2026-101
```

---

### 🔴 Stage 4 — Final Notice (23 Days Overdue)

```text
Subject: FINAL NOTICE – Invoice #INV-2026-101 – Immediate Action Required
Tone   : Stern & Urgent

Dear ABC Technologies Pvt Ltd Team,

This is the final notice regarding Invoice #INV-2026-101.

The payment is now 23 days overdue.

This is your final opportunity to settle the amount
before escalation to our collections partner.

Payment Link:
https://pay.company.com/INV-2026-101
```

---

### 🚨 Stage 5 — Manager Escalation (38 Days Overdue)

```text
SENDING ESCALATION EMAIL TO MANAGER

To      : finance.manager@company.com
Subject : Escalation Required: Invoice INV-2026-101

Body:
Invoice INV-2026-101 for client ABC Technologies Pvt Ltd
is 38 days overdue and requires manual review.
```

---

## 👨‍💼 Human-in-the-Loop Approval

```text
Approve or Reject this email? (approve/reject):
```

Finance teams can review and approve every generated email before sending.

---

## 📊 Workflow Summary Example

```text
days_overdue      : 18
stage_key         : 3rd Follow-Up
validation_status : approved
retry_count       : 0
send_status       : sent
```

---

## 📝 Audit Log Example

```text
invoice_no           : INV-2026-101
client               : ABC Technologies Pvt Ltd
amount               : 45250.75
days_overdue         : 23
stage_key            : 4th Follow-Up
tone_used            : Stern & Urgent
validation_status    : approved
send_status          : sent
retry_count          : 0
max_retries          : 3
```

---

## 🛠️ Tech Stack

- Python
- LangGraph
- LangChain
- Mistral AI
- Streamlit
- Pydantic
- dotenv

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Financial_analyzer_agent
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Environment

**Windows**
```bash
.venv\Scripts\activate
```

**Linux / macOS**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Create `.env`

```env
MISTRAL_API_KEY=your_api_key_here
```

---

## 🔑 Get a Free Mistral API Key

1. Sign up at https://console.mistral.ai/
2. Open https://admin.mistral.ai/organization/api-keys
3. Create a new API key
4. Copy it into your `.env` file

---

## ▶️ Run Streamlit Dashboard

```bash
streamlit run app.py
```

---

## 💻 Run CLI Version

```bash
python run_cli.py
```

---

## 📂 Project Structure

```text
Financial_analyzer_agent/
├── app.py
├── run_cli.py
├── graph.py
├── nodes/
├── models.py
├── prompts.py
├── utils/
├── logs/
├── requirements.txt
└── README.md
```

---

## 🎯 Real-World Use Cases

- Accounts receivable automation
- Credit control
- Payment collection reminders
- Finance team productivity
- ERP and accounting integrations

---

## 🔮 Future Enhancements

- SMTP integration
- ERP integrations (SAP, Oracle, Zoho Books)
- Multi-language email generation
- Analytics dashboard
- Scheduled follow-ups
- PDF invoice attachment support

---

## ⭐ Why This Project Stands Out

This project showcases advanced engineering concepts frequently evaluated in AI and backend interviews:

- Multi-step LangGraph workflows
- Structured LLM outputs
- Human-in-the-loop systems
- Retry and checkpoint recovery
- Escalation logic
- Enterprise audit logging
- Streamlit product development

---

## 📜 License

MIT License

---

<div align="center">

### ⭐ If you found this project useful, consider giving it a star!

</div>
