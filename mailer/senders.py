import logging
import threading
from typing import List

from django.core.mail import EmailMessage

from .exceptions import EmailError

logger = logging.getLogger(__name__)


class EmailSender(threading.Thread):
    def __init__(self, messages: List[EmailMessage]):
        super().__init__()
        for message in messages:
            if not (message and isinstance(message, EmailMessage)):
                raise EmailError()

        self.messages = messages

    def run(self):
        self.send_email_messages()

    def send_email_messages(self):
        for message in self.messages:
            try:
                message.send()
                logger.info('Message to {0} has been successfully sent'.format(message.to), )

            except Exception as e:
                raise EmailError()
