import os
import smtplib
from email.message import EmailMessage


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(to_email: str, subject: str, body: str):
    """
    Send a plain-text email using Gmail SMTP.
    Credentials are read from environment variables.
    """

    smtp_user = os.getenv("HMS_EMAIL_USER")
    smtp_password = os.getenv("HMS_EMAIL_PASSWORD")

    if not smtp_user or not smtp_password:
        raise RuntimeError("Email credentials not configured")

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
