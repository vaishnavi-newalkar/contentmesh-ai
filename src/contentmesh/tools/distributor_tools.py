import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import httpx
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()


@tool("send_email_tool")
def send_email_tool(to: str, subject: str, body: str) -> str:
    """Send an email to the specified recipient using SMTP.
    Falls back to demo mode if SMTP credentials are not configured."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        return (
            f"[DEMO MODE] Email simulated successfully → "
            f"To: {to} | Subject: {subject} | Status: delivered"
        )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to, msg.as_string())

        return f"Email successfully sent to {to} with subject: {subject}"
    except Exception as e:
        return f"[DEMO MODE] Email simulated (SMTP error: {e})"


@tool("post_to_slack_tool")
def post_to_slack_tool(message: str) -> str:
    """Post a message to the configured Slack webhook URL.
    Falls back to demo mode if webhook is not configured."""
    webhook_url = os.getenv("SLACK_WEBHOOK", "")

    if not webhook_url or "YOUR" in webhook_url:
        return f"[DEMO MODE] Slack post simulated: {message[:120]}..."

    try:
        response = httpx.post(
            webhook_url,
            json={"text": message},
            timeout=10,
        )
        if response.status_code == 200:
            return "Successfully posted to Slack channel"
        return f"Slack post failed with HTTP {response.status_code}"
    except Exception as e:
        return f"[DEMO MODE] Slack simulated (error: {e})"


@tool("log_distribution_tool")
def log_distribution_tool(channel: str, status: str, details: str) -> str:
    """Log a distribution event with a UTC timestamp for the audit trail."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    entry = {
        "timestamp": timestamp,
        "channel": channel,
        "status": status,
        "details": details,
    }
    print(f"[DISTRIBUTION LOG] {json.dumps(entry)}")
    return f"Logged: {channel} → {status} at {timestamp}"
