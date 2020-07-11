from typing import Type

from mailer.builders import BaseEmailBuilder, VerificaitonCodeEmailBuilder
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
