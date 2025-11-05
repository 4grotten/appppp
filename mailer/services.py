from typing import Type

from mailer.builders import (
    BaseEmailBuilder,
    VerificaitonCodeEmailBuilder,
    ShadowBanEmailBuilder,
    VerificationOrganizationsEmailBuilder,
    PaymentSystemOrganizationsEmailBuilder,
    WholesaleOrganizationsEmailBuilder,
    InvoiceEmailBuilder,
)
from mailer.senders import EmailSender


class MailerService:
    @classmethod
    def _send(cls, builder: Type[BaseEmailBuilder], **kwargs):
        message = builder.build_message(**kwargs)
        email_sender = EmailSender([message])
        email_sender.start()

    @classmethod
    def send_verification_code_email(cls, email: str, code: str):
        cls._send(VerificaitonCodeEmailBuilder, email=email, code=code)

    @classmethod
    def send_shadow_ban_email(cls, email, org_id, send_time):
        cls._send(
            ShadowBanEmailBuilder, email=email, org_id=org_id, send_time=send_time
        )

    @classmethod
    def send_verifications_email(cls, email, org_id, send_time):
        cls._send(
            VerificationOrganizationsEmailBuilder,
            email=email,
            org_id=org_id,
            send_time=send_time,
        )

    @classmethod
    def send_payment_verification_email(
        cls, email, org_id, send_time, payment_system_name
    ):
        cls._send(
            PaymentSystemOrganizationsEmailBuilder,
            email=email,
            org_id=org_id,
            send_time=send_time,
            payment_system_name=payment_system_name,
        )

    @classmethod
    def send_wholesale_verification_email(cls, email, org_id, send_time):
        cls._send(
            WholesaleOrganizationsEmailBuilder,
            email=email,
            org_id=org_id,
            send_time=send_time,
        )

    @classmethod
    def send_invoice_url_email(cls, email, invoice_url, send_time):
        cls._send(
            InvoiceEmailBuilder,
            email=email,
            invoice_url=invoice_url,
            send_time=send_time,
        )
