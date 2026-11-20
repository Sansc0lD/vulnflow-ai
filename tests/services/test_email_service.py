"""Unit tests for SMTP email sender & templates — apps/api/app/services/email_service.py."""

import smtplib
from email.message import EmailMessage

import pytest
from app.services.email_service import (
    SMTPEmailSender,
    send_invitation_email,
    send_password_reset_email,
)


def test_smtp_sender_skips_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def _boom(*args: object, **kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("SMTP should not be called when disabled")

    monkeypatch.setattr(smtplib, "SMTP", _boom)
    sender = SMTPEmailSender(host="127.0.0.1", port=1025, from_email="no@test.local", enabled=False)

    assert (
        sender.send_email(to_email="u@x.com", subject="Hi", html_body="<p>Hi</p>", text_body="Hi")
        is False
    )
    assert called is False


def test_smtp_sender_sends_and_handles_connection_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_messages: list[EmailMessage] = []

    class _FakeSMTP:
        def __init__(self, host: str, port: int, timeout: float = 5.0) -> None:
            self.host = host
            self.port = port
            self.tls_called = False
            self.logged_in: tuple[str, str] | None = None

        def __enter__(self) -> "_FakeSMTP":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def starttls(self) -> None:
            self.tls_called = True

        def login(self, user: str, password: str) -> None:
            self.logged_in = (user, password)

        def send_message(self, msg: EmailMessage) -> None:
            sent_messages.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)
    sender = SMTPEmailSender(
        host="mailpit",
        port=1025,
        from_email="noreply@vulnflow.local",
        username="u",
        password="p",
        use_tls=True,
        enabled=True,
    )
    assert (
        sender.send_email(
            to_email="pentester@corp.com",
            subject="Test",
            html_body="<p>Hello</p>",
            text_body="Hello",
        )
        is True
    )
    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "pentester@corp.com"

    def _fail_smtp(*args: object, **kwargs: object) -> object:
        raise OSError("connection refused")

    monkeypatch.setattr(smtplib, "SMTP", _fail_smtp)
    assert (
        sender.send_email(
            to_email="pentester@corp.com",
            subject="Test",
            html_body="<p>Hello</p>",
            text_body="Hello",
        )
        is False
    )


def test_invitation_and_reset_email_helpers_escape_html() -> None:
    captured: list[tuple[str, str, str, str]] = []

    class _RecordingSender:
        def send_email(
            self, *, to_email: str, subject: str, html_body: str, text_body: str
        ) -> bool:
            captured.append((to_email, subject, html_body, text_body))
            return True

    sender = _RecordingSender()
    assert (
        send_invitation_email(
            sender,
            to_email="dev@corp.com",
            workspace_name="<script>alert(1)</script>",
            role="PENTESTER",
            invitation_token="tok+1/2=3",
            app_base_url="http://localhost:5173/",
        )
        is True
    )
    assert (
        send_password_reset_email(
            sender,
            to_email="dev@corp.com",
            reset_token="rst.123",
            app_base_url="http://localhost:5173",
        )
        is True
    )

    assert len(captured) == 2
    assert "VulnFlow AI Workspace Invitation:" in captured[0][1]
    assert "Accept Invitation" in captured[0][2]
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in captured[0][2]
    assert "http://localhost:5173/app/register?invite=tok%2B1%2F2%3D3" in captured[0][3]
    assert captured[1][1] == "Reset Your VulnFlow AI Password"
    assert "Reset Password" in captured[1][2]
    assert "http://localhost:5173/app/reset-password?token=rst.123" in captured[1][3]
