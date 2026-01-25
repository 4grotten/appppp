"""OTP Bot services package.

Services:
- OTPService: OTP code generation and verification
- WAHAOTPClient: WhatsApp messaging via WAHA
- FinanceAIService: AI responses for EasyCard questions
- ElevenLabsService: Speech-to-Text and Text-to-Speech
"""

from .otp_service import OTPService
from .waha_otp import WAHAOTPClient, WAHAOTPError
from .ai_service import FinanceAIService, FinanceAIServiceError
from .elevenlabs import ElevenLabsService, ElevenLabsError

__all__ = [
    "OTPService",
    "WAHAOTPClient",
    "WAHAOTPError",
    "FinanceAIService",
    "FinanceAIServiceError",
    "ElevenLabsService",
    "ElevenLabsError",
]
