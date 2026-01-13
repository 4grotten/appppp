from django import forms
from django.utils.translation import gettext_lazy as _


class SendCodeForm(forms.Form):
    """Form to initiate phone code sending."""
    confirm = forms.BooleanField(
        required=True,
        label=_("I confirm I want to send verification code to this phone"),
        help_text=_("A verification code will be sent via Telegram/SMS"),
    )


class VerifyCodeForm(forms.Form):
    """Form to verify phone code."""
    code = forms.CharField(
        max_length=10,
        required=True,
        label=_("Verification Code"),
        help_text=_("Enter the code sent to your Telegram/phone"),
        widget=forms.TextInput(attrs={
            "placeholder": "12345",
            "autofocus": True,
            "style": "font-size: 18px; letter-spacing: 2px; width: 150px;",
        }),
    )


class Verify2FAForm(forms.Form):
    """Form to verify 2FA password."""
    password = forms.CharField(
        max_length=255,
        required=True,
        label=_("2FA Password"),
        help_text=_("Enter your Telegram 2FA password"),
        widget=forms.PasswordInput(attrs={
            "placeholder": "Your 2FA password",
            "autofocus": True,
        }),
    )


class TestMessageForm(forms.Form):
    """Form to send a test message."""
    chat = forms.CharField(
        max_length=100,
        required=True,
        label=_("Chat/Username"),
        help_text=_("Username (e.g., @BotFather) or chat ID to send message to"),
        widget=forms.TextInput(attrs={
            "placeholder": "@username or chat_id",
        }),
    )
    message = forms.CharField(
        max_length=500,
        required=True,
        label=_("Message"),
        help_text=_("Message text to send"),
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Test message...",
        }),
    )
