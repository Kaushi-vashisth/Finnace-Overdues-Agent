# Finance Credit Follow-Up AI Agent

An enterprise-grade AI workflow that automates overdue invoice follow-up emails using LangGraph, Mistral AI, and Streamlit.

## Features

- Invoice input and overdue calculation
- Dynamic follow-up stage selection
- Personalized email generation
- Automated validation
- Human-in-the-loop approval
- Retry with feedback
- Escalation to finance manager
- Audit logging
- Streamlit dashboard and CLI runner

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Create a `.env` file:
   MISTRAL_API_KEY=your_api_key_here
4. Run the Streamlit app:
   streamlit run app.py

## Get a Free Mistral API Key

1. Sign up at https://console.mistral.ai/
2. Open https://admin.mistral.ai/organization/api-keys
3. Create a new API key and copy it into your `.env` file.

## Run CLI

python run_cli.py
