from organizations.models import (
    ZinaPayOrganizationPaymentSystem as OriginalZinaPayOrganizationPaymentSystem,
)


class ZinaPayOrganizationPaymentSystem(OriginalZinaPayOrganizationPaymentSystem):
    """Настройки ZinaPay для организаций (proxy)"""
    class Meta:
        proxy = True
        verbose_name = "Настройки ZinaPay для организации"
        verbose_name_plural = "ZinaPay - Настройки организаций"
from organizations.models import (
    MaalyPayOrganizationPaymentSystem as OriginalMaalyPayOrganizationPaymentSystem,
)
from organizations.models import (
    PaymentSystemMethod as OriginalPaymentSystemMethod,
)
from organizations.models import (
    RegionalPaymentSystemSettings as OriginalRegionalPaymentSystemSettings,
)


class RegionalPaymentSystemSettings(OriginalRegionalPaymentSystemSettings):
    """Proxy модель для группировки в Payments приложении"""
    class Meta:
        proxy = True
        verbose_name = "Regional Payment System Settings"
        verbose_name_plural = "Regional Payment System Settings"


# Proxy модели для каждой платёжной системы
class FreedomPaySettings(OriginalRegionalPaymentSystemSettings):
    """Настройки FreedomPay по регионам"""
    class Meta:
        proxy = True
        verbose_name = "FreedomPay"
        verbose_name_plural = "FreedomPay - Настройки регионов"


class PaySySettings(OriginalRegionalPaymentSystemSettings):
    """Настройки PaySy по регионам"""
    class Meta:
        proxy = True
        verbose_name = "PaySy"
        verbose_name_plural = "PaySy - Настройки регионов"


class LibersaveSettings(OriginalRegionalPaymentSystemSettings):
    """Настройки Libersave по регионам"""
    class Meta:
        proxy = True
        verbose_name = "Libersave"
        verbose_name_plural = "Libersave - Настройки регионов"


class BetapaySettings(OriginalRegionalPaymentSystemSettings):
    """Настройки Betapay по регионам"""
    class Meta:
        proxy = True
        verbose_name = "Betapay"
        verbose_name_plural = "Betapay - Настройки регионов"


class CryptoCloudSettings(OriginalRegionalPaymentSystemSettings):
    """Настройки CryptoCloud по регионам"""
    class Meta:
        proxy = True
        verbose_name = "CryptoCloud"
        verbose_name_plural = "CryptoCloud - Настройки регионов"


class MaalyPaySettings(OriginalRegionalPaymentSystemSettings):
    """Настройки MaalyPay по регионам"""
    class Meta:
        proxy = True
        verbose_name = "MaalyPay"
        verbose_name_plural = "MaalyPay - Настройки регионов"


class MaalyPayOrganizationPaymentSystem(OriginalMaalyPayOrganizationPaymentSystem):
    """Настройки MaalyPay для организаций"""
    class Meta:
        proxy = True
        verbose_name = "Настройки MaalyPay для организации"
        verbose_name_plural = "MaalyPay - Настройки организаций"


class PaymentSystemMethod(OriginalPaymentSystemMethod):
    """Proxy модель для группировки в Payments приложении"""
    class Meta:
        proxy = True
        verbose_name = "Payment System Method"
        verbose_name_plural = "Payment System Methods"
