from django.contrib import admin
from payments.models import (
    RegionalPaymentSystemSettings,
    MaalyPayOrganizationPaymentSystem,
    PaymentSystemMethod
)
from organizations.admin import (
    RegionalPaymentSystemSettingsAdmin,
    MaalyPayAdmin,
    PaymentSystemMethodAdmin
)

# Register proxy payment models under payments app
admin.site.register(RegionalPaymentSystemSettings, RegionalPaymentSystemSettingsAdmin)
admin.site.register(MaalyPayOrganizationPaymentSystem, MaalyPayAdmin)
admin.site.register(PaymentSystemMethod, PaymentSystemMethodAdmin)
