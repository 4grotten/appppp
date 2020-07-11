import logging
from abc import ABC, abstractmethod

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader, Template

from .constants import VERIFICATION_CODE_EMAIL_TITLE

logger = logging.getLogger(__name__)


class BaseEmailBuilder(ABC):
    @property
    @abstractmethod
    def TEMPLATE_NAME(self):
        pass

    @property
    @abstractmethod
    def FROM_EMAIL(self):
        pass

    @classmethod
    @abstractmethod
    def build_message(cls, email: str, **kwargs) -> EmailMessage:
        pass


class VerificaitonCodeEmailBuilder(BaseEmailBuilder):
    TEMPLATE_NAME = 'temporary_code_email.html'
    FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

    @classmethod
    def _get_rendered_template(cls, context: dict) -> Template:
        template = loader.get_template(cls.TEMPLATE_NAME)
        return template.render(context)

    @classmethod
    def build_message(cls, email: str, **kwargs) -> EmailMessage:
        """
        kwargs dict should contain "code" key
        """

        context = {
            'code': kwargs['code'],
        }

        body = cls._get_rendered_template(context)

        message = EmailMessage(
            subject=VERIFICATION_CODE_EMAIL_TITLE,
            body=body,
            to=[email],
            from_email=cls.FROM_EMAIL
        )
        message.content_subtype = 'html'
        return message
