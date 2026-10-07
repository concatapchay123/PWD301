"""Disposable SQL Server email outbox/retry probe for the notification audit.

This probe creates only the exact audit database used by grading-runtime-probe.py,
exercises the real FAILED -> Admin API retry -> queue SENT path, and removes the
database in a finally block. The mail transport is an in-process capture client;
it proves the application outbox and recipient boundary without sending mail to an
external address.
"""

from __future__ import annotations

import json
import runpy
import smtplib
import socketserver
import threading
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import default
from pathlib import Path


class _SMTPHandler(socketserver.StreamRequestHandler):
    """Minimal loopback SMTP sink for a disposable transport probe."""

    def _send(self, message: str) -> None:
        self.wfile.write(message.encode("ascii"))
        self.wfile.flush()

    def handle(self) -> None:
        self._send("220 PWD301 audit SMTP sink\r\n")
        while True:
            raw_line = self.rfile.readline()
            if not raw_line:
                return
            command = raw_line.decode("ascii", errors="replace").strip()
            verb = command.split(" ", 1)[0].upper()
            if verb == "EHLO" or verb == "HELO":
                self._send("250-localhost\r\n250-SIZE 10485760\r\n250-8BITMIME\r\n250 OK\r\n")
            elif verb == "MAIL":
                self._send("250 2.1.0 OK\r\n")
            elif verb == "RCPT":
                self._send("250 2.1.5 OK\r\n")
            elif verb == "DATA":
                self._send("354 End data with <CR><LF>.<CR><LF>\r\n")
                message_lines: list[bytes] = []
                while True:
                    data_line = self.rfile.readline()
                    if data_line in (b"", b".\r\n"):
                        break
                    if data_line.startswith(b".."):
                        data_line = data_line[1:]
                    message_lines.append(data_line)
                self.server.messages.append(b"".join(message_lines))
                self._send("250 2.0.0 queued\r\n")
            elif verb == "RSET" or verb == "NOOP":
                self._send("250 OK\r\n")
            elif verb == "QUIT":
                self._send("221 2.0.0 Bye\r\n")
                return
            else:
                self._send("502 Command not implemented\r\n")


class _SMTPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _SMTPHandler)
        self.messages: list[bytes] = []


class _SMTPMailClient:
    """Real SMTP client used only against the loopback audit sink."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def send(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> None:
        message = EmailMessage()
        message["From"] = "no-reply@pwd301.local"
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(body_text)
        with smtplib.SMTP(self.host, self.port, timeout=5) as client:
            client.send_message(message)


def load_grading_probe() -> dict[str, object]:
    path = Path(__file__).with_name("grading-runtime-probe.py")
    return runpy.run_path(str(path), run_name="notification_grading_probe")


def main() -> None:
    namespace = load_grading_probe()
    base_url = namespace["base_url"]
    prepare = namespace["prepare"]
    audit_app = namespace["audit_app"]
    cleanup = namespace["cleanup"]
    database_name = namespace["DATABASE_NAME"]

    from pwd301.extensions import db
    from pwd301.models.identity import User
    from pwd301.models.notification_audit import EmailDelivery
    from pwd301.models.types import utc_now
    from pwd301.services.email_service import (
        MockMailClient,
        enqueue_email,
        process_email_queue,
    )
    from pwd301.services.notification_service import emit_event

    url = base_url()
    prepare(url)
    try:
        app = audit_app(url)
        with app.app_context():
            admin = db.session.query(User).filter_by(email="admin@pwd301.local").one()
            recipient = db.session.query(User).filter_by(email="student4@pwd301.local").one()
            # Seed data may contain unrelated outbox rows. Mark those historical
            # fixtures sent so this disposable probe has one authoritative target.
            for seeded_delivery in db.session.query(EmailDelivery).all():
                seeded_delivery.status = "SENT"
                seeded_delivery.sent_at = utc_now()
                seeded_delivery.next_attempt_at = None
            db.session.commit()
            event = emit_event(
                event_type="EMAIL_DELIVERY_AUDIT",
                payload={"scope": "disposable_email_outbox_probe"},
                actor_user_id=admin.id,
                target_type="EMAIL",
                session=db.session,
            )
            delivery = enqueue_email(
                recipient_email=recipient.email,
                subject="PWD301 audit email",
                body_text="Disposable notification email outbox probe.",
                template_code="AUDIT_EMAIL_RETRY",
                notification_event_id=event.id,
                recipient_user_id=recipient.id,
                session=db.session,
            )
            db.session.commit()

            failed = process_email_queue(
                max_retries=1,
                mail_client=MockMailClient(should_fail=True, fail_message="audit sink failure"),
                session=db.session,
            )
            db.session.commit()
            db.session.refresh(delivery)
            failed_status = delivery.status

            client = app.test_client()
            login = client.post(
                "/api/v1/auth/token",
                json={"email": admin.email, "password": "Password123!"},
            )
            token = login.get_json()["access_token"]
            retry_response = client.post(
                "/api/admin/emails/retry-failed",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )
            retry_body = retry_response.get_json()
            db.session.expire_all()
            retried = db.session.query(EmailDelivery).filter_by(id=delivery.id).one()

            smtp_server = _SMTPServer()
            smtp_thread = threading.Thread(
                target=smtp_server.serve_forever,
                name="pwd301-audit-smtp",
                daemon=True,
            )
            smtp_thread.start()
            try:
                smtp_host, smtp_port = smtp_server.server_address
                sent = process_email_queue(
                    mail_client=_SMTPMailClient(smtp_host, smtp_port),
                    session=db.session,
                )
                db.session.commit()
                db.session.refresh(retried)
            finally:
                smtp_server.shutdown()
                smtp_server.server_close()
                smtp_thread.join(timeout=5)

            captured = [
                {
                    "recipient": message.get("To"),
                    "subject": message.get("Subject"),
                }
                for message in (
                    BytesParser(policy=default).parsebytes(raw) for raw in smtp_server.messages
                )
            ]

            result = {
                "database": database_name,
                "login_status": login.status_code,
                "forced_failure": failed,
                "failed_status": failed_status,
                "retry_http_status": retry_response.status_code,
                "retry_body": retry_body,
                "queue_success": sent,
                "final_status": retried.status,
                "smtp_messages_captured": captured,
                "recipient_boundary": retried.recipient_email_snapshot,
            }
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    finally:
        cleanup(url, database_name)


if __name__ == "__main__":
    main()
