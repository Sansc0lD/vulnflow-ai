"""Transactional email sender via SMTP (Mailpit in local Docker) — UC-02a, UC-05."""

import logging
import os
import smtplib
import urllib.parse
from email.message import EmailMessage
from html import escape
from typing import Protocol

logger = logging.getLogger("vulnflow.email")


class EmailSender(Protocol):
    def send_email(
        self, *, to_email: str, subject: str, html_body: str, text_body: str
    ) -> bool: ...


class SMTPEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        from_email: str,
        username: str = "",
        password: str = "",
        use_tls: bool = False,
        enabled: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._from_email = from_email
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._enabled = enabled

    def send_email(self, *, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        if not self._enabled:
            logger.info("SMTP disabled; skipping email to %s (%s)", to_email, subject)
            return False

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._from_email
        msg["To"] = to_email
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        try:
            with smtplib.SMTP(self._host, self._port, timeout=5.0) as smtp:
                if self._use_tls:
                    smtp.starttls()
                if self._username and self._password:
                    smtp.login(self._username, self._password)
                smtp.send_message(msg)
            return True
        except Exception as exc:
            logger.warning("Failed to send email via SMTP %s:%s: %s", self._host, self._port, exc)
            return False


def get_email_sender() -> EmailSender:
    return SMTPEmailSender(
        host=os.environ.get("SMTP_HOST", "127.0.0.1"),
        port=int(os.environ.get("SMTP_PORT", "1025")),
        from_email=os.environ.get("SMTP_FROM", "noreply@vulnflow.local"),
        username=os.environ.get("SMTP_USERNAME", ""),
        password=os.environ.get("SMTP_PASSWORD", ""),
        use_tls=os.environ.get("SMTP_USE_TLS", "false").lower() == "true",
        enabled=os.environ.get("SMTP_ENABLED", "true").lower() != "false",
    )


def get_app_base_url() -> str:
    return os.environ.get("APP_BASE_URL", "http://localhost:5173").rstrip("/")


def send_invitation_email(
    sender: EmailSender,
    *,
    to_email: str,
    workspace_name: str,
    role: str,
    invitation_token: str,
    app_base_url: str | None = None,
) -> bool:
    base = (app_base_url or get_app_base_url()).rstrip("/")
    encoded_token = urllib.parse.quote(invitation_token, safe="")
    encoded_email = urllib.parse.quote(to_email, safe="")
    invite_url = f"{base}/app/register?invite={encoded_token}&email={encoded_email}"

    subject = f"VulnFlow AI Workspace Invitation: {workspace_name}"
    text_body = (
        f"You have been invited to join the '{workspace_name}' workspace as {role}.\n\n"
        f"Open the link below to register or accept the invitation:\n{invite_url}\n\n"
        f"Invitation token (valid for 7 days): {invitation_token}\n"
    )
    html_body = (
        "<h2>VulnFlow AI Workspace Invitation</h2>"
        f"<p>You have been invited to join workspace <strong>{escape(workspace_name)}</strong> "
        f"with the role <strong>{escape(role)}</strong>.</p>"
        f'<p><a href="{escape(invite_url)}">Accept Invitation</a></p>'
        f"<p>Token (valid for 7 days): <code>{escape(invitation_token)}</code></p>"
    )
    return sender.send_email(
        to_email=to_email, subject=subject, html_body=html_body, text_body=text_body
    )


def send_password_reset_email(
    sender: EmailSender,
    *,
    to_email: str,
    reset_token: str,
    app_base_url: str | None = None,
) -> bool:
    base = (app_base_url or get_app_base_url()).rstrip("/")
    encoded_token = urllib.parse.quote(reset_token, safe="")
    reset_url = f"{base}/app/reset-password?token={encoded_token}"

    subject = "Reset Your VulnFlow AI Password"
    text_body = (
        "We received a request to reset the password for your VulnFlow AI account.\n\n"
        f"Use the link below (valid for 15 minutes):\n{reset_url}\n\n"
        "If you did not request a password reset, you can safely ignore this email.\n"
    )
    html_body = (
        "<h2>Reset Your VulnFlow AI Password</h2>"
        "<p>Use the link below to set a new password for your account (valid for 15 minutes):</p>"
        f'<p><a href="{escape(reset_url)}">Reset Password</a></p>'
        "<p>If you did not request a password reset, you can safely ignore this email.</p>"
    )
    return sender.send_email(
        to_email=to_email, subject=subject, html_body=html_body, text_body=text_body
    )
