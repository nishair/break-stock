import smtplib
from email.mime.text import MIMEText
from config import EMAIL_ENABLED, EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_TO


def send_notification(message: str):
    if EMAIL_ENABLED:
        send_email("Price Alert Triggered", message)
    # Always print to console as fallback
    print(f"[ALERT] {message}")


def send_email(subject: str, body: str):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_TO

        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"[ALERT] Failed to send email: {e}")
