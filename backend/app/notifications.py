from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from sqlalchemy import select

from .db import NotificationOutboxModel


class EmailSettings:
    def __init__(self) -> None:
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender = os.getenv("EMAIL_FROM", "decision-wave@localhost")
        self.use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"


def queue_email_notification(session, recipient: str, subject: str, body: str) -> None:
    session.add(
        NotificationOutboxModel(
            channel="email",
            recipient=recipient,
            subject=subject,
            body=body,
        )
    )


def send_email(settings: EmailSettings, recipient: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def process_email_outbox(session, limit: int = 20) -> dict:
    settings = EmailSettings()
    queued = session.scalars(
        select(NotificationOutboxModel)
        .where(NotificationOutboxModel.channel == "email")
        .order_by(NotificationOutboxModel.created_at.asc())
        .limit(limit)
    ).all()

    sent = 0
    failed = 0
    errors: list[str] = []

    for item in queued:
        try:
            send_email(settings, item.recipient, item.subject, item.body)
            session.delete(item)
            sent += 1
        except Exception as exc:
            failed += 1
            errors.append(f"outbox_id={item.id}: {exc}")

    return {"attempted": len(queued), "sent": sent, "failed": failed, "errors": errors}
