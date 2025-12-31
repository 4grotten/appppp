
class RegionalPaymentSystemService:

    PAYMENT_SYSTEMS = {
        1: {
            'name': 'FreedomPay',
            'currency': 'KGS',
            'confirmed_field': 'freedompay_confirmed',
            'activated_field': 'freedompay_activated'
        },
        2: {
            'name': 'PaySy',
            'currency': 'USD',
            'confirmed_field': 'paysy_confirmed',
            'activated_field': 'paysy_activated'
        },
        3: {
            'name': 'Libersave',
            'currency': 'EUR',
            'confirmed_field': 'libersave_confirmed',
            'activated_field': 'libersave_activated'
        },
        4: {
            'name': 'Betapay',
            'currency': 'EUR',
            'confirmed_field': 'betapay_confirmed',
            'activated_field': 'betapay_activated'
        },
        5: {
            'name': 'CryptoCloud',
            'currency': 'USD',
            'confirmed_field': 'cryptocloud_confirmed',
            'activated_field': 'cryptocloud_activated'
        },
        6: {
            'name': 'MaalyPay',
            'currency': 'AED',
            'confirmed_field': 'maaly_pay_confirmed',
            'activated_field': 'maaly_pay_activated'
        },
    }

    @classmethod
    def get_model(cls):
        from organizations.models import RegionalPaymentSystemSettings
        return RegionalPaymentSystemSettings

    @classmethod
    def is_enabled_in_region(cls, country, payment_system_id: int, organization=None) -> bool:
        model = cls.get_model()
        setting = model.objects.filter(
            country=country,
            payment_system_id=payment_system_id
        ).prefetch_related('allowed_organizations').first()

        if setting is None:
            return True

        if organization and setting.allowed_organizations.filter(id=organization.id).exists():
            return True

        return setting.is_enabled_in_region

    @classmethod
    def is_available_for_request(cls, country, payment_system_id: int) -> bool:
        model = cls.get_model()
        setting = model.objects.filter(
            country=country,
            payment_system_id=payment_system_id
        ).first()

        if setting is None:
            return True

        return setting.is_available_for_request and setting.is_enabled_in_region

    @classmethod
    def get_available_for_organization(cls, organization) -> list:
        country = organization.country
        result = []

        for ps_id, ps_info in cls.PAYMENT_SYSTEMS.items():
            if not cls.is_enabled_in_region(country, ps_id, organization):
                continue

            is_confirmed = getattr(organization, ps_info['confirmed_field'], False)
            is_activated = getattr(organization, ps_info['activated_field'], False)
            can_request = cls.is_available_for_request(country, ps_id)

            result.append({
                'id': ps_id,
                'name': ps_info['name'],
                'currency': ps_info['currency'],
                'is_confirmed': is_confirmed,
                'is_activated': is_activated,
                'is_available_for_request': can_request and not is_confirmed,
            })

        return result

    @classmethod
    def get_confirmed_for_organization(cls, organization) -> list:

        country = organization.country
        result = []

        for ps_id, ps_info in cls.PAYMENT_SYSTEMS.items():
            if not cls.is_enabled_in_region(country, ps_id, organization):
                continue

            is_confirmed = getattr(organization, ps_info['confirmed_field'], False)
            if not is_confirmed:
                continue

            is_activated = getattr(organization, ps_info['activated_field'], False)

            result.append({
                'id': ps_id,
                'name': ps_info['name'],
                'currency': ps_info['currency'],
                'is_active': is_activated,
            })

        return result

    @classmethod
    def get_payment_system_info(cls, payment_system_id: int) -> dict:
        return cls.PAYMENT_SYSTEMS.get(payment_system_id)
