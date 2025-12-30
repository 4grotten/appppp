from organizations.models import (
    RegionalPaymentSystemSettings as OriginalRegionalPaymentSystemSettings,
    MaalyPayOrganizationPaymentSystem as OriginalMaalyPayOrganizationPaymentSystem,
    PaymentSystemMethod as OriginalPaymentSystemMethod,
)


class RegionalPaymentSystemSettings(OriginalRegionalPaymentSystemSettings):
    """Proxy модель для группировки в Payments приложении"""
    class Meta:
        proxy = True
        verbose_name = "Regional Payment System Settings"
        verbose_name_plural = "Regional Payment System Settings"


class MaalyPayOrganizationPaymentSystem(OriginalMaalyPayOrganizationPaymentSystem):
    """Proxy модель для группировки в Payments приложении"""
    class Meta:
        proxy = True
        verbose_name = "Maaly Pay Organization Payment System"
        verbose_name_plural = "Maaly Pay Organization Payment Systems"


class PaymentSystemMethod(OriginalPaymentSystemMethod):
    """Proxy модель для группировки в Payments приложении"""
    class Meta:
        proxy = True
        verbose_name = "Payment System Method"
        verbose_name_plural = "Payment System Methods"
