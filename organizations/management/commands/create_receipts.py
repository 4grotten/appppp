from django.core.management.base import BaseCommand
from django.conf import settings
from organizations.models import (
    OrganizationInvoiceInfo,
    Organization,
    UserOrgSubscription,
    RegionalTariff,
)
from organizations.services.receipts_services import ReceiptService


class Command(BaseCommand):
    help = "Создает Receipt'ы для организаций у которых не создался receipt"

    def handle(self, *args, **options):
        org_info_qs = OrganizationInvoiceInfo.objects.get(id=46)
        organizations = (
            UserOrgSubscription.objects.filter(
                is_active=True, transaction__isnull=False
            )
            .select_related("organization")
            .exclude(organization_id=2796)
        )

        for org in organizations:
            self.stdout.write(
                self.style.WARNING(
                    f"STARTING MAKE A RECEIPT FOR {org.organization.title}"
                )
            )
            ReceiptService.create_receipt_from_management_as_crypto_cloud(
                org, org_info_qs
            )
        self.stdout.write(self.style.SUCCESS(f"SUCCESFULLY UPDATED RECEIPTS!"))
