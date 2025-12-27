"""
MaalyPay Staging/Dev Testing Script
Uses EXISTING organizations and data from the database

Run: docker exec backend-django-1 python test_maalypay_staging.py

Options:
  --org-id=<ID>     - Test with specific organization ID
  --real-api        - Use real MaalyPay API (default: simulation)
  --list-orgs       - List available organizations with MaalyPay
"""
import json
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.base")
django.setup()

from common.models import Currency
from organizations.models import (
    MaalyPayOrganizationPaymentSystem,
    Organization,
)
from organizations.services.maalypay_service import MaalyPayService
from transactions.models import Transaction


class MaalyPayStagingTest:
    """Test MaalyPay with existing staging/dev data"""

    def __init__(self, org_id=None, use_real_api=False):
        self.org_id = org_id
        self.use_real_api = use_real_api
        self.org = None
        self.config = None
        self.transaction = None

    def print_header(self, text):
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)

    def list_available_organizations(self):
        """List all organizations with MaalyPay configured"""
        self.print_header("Available Organizations with MaalyPay")

        configs = MaalyPayOrganizationPaymentSystem.objects.select_related(
            'organization'
        ).all()

        if not configs:
            print("\n❌ No organizations with MaalyPay configuration found!")
            print("\nTo add MaalyPay to an organization:")
            print("1. Go to organization settings in admin/frontend")
            print("2. Add payment system: MaalyPay (ID: 6)")
            print("3. Enter merchant_id and api_key")
            return []

        print(f"\nFound {configs.count()} organization(s) with MaalyPay:\n")

        orgs = []
        for config in configs:
            org = config.organization
            print(f"📊 Organization ID: {org.id}")
            print(f"   Title: {org.title}")
            print(f"   Owner: {org.owner.phone_number if org.owner else 'N/A'}")
            print(f"   Activated: {org.maaly_pay_activated}")
            print(f"   Merchant ID: {config.merchant_id}")
            print(f"   API Key: {config.api_key[:20]}..." if config.api_key else "   API Key: Not set")
            print(f"   Bank Info: {config.bank_info or 'Not set'}")
            print()

            orgs.append({
                'id': org.id,
                'title': org.title,
                'config': config,
            })

        return orgs

    def select_organization(self):
        """Select organization to test with"""
        self.print_header("Organization Selection")

        if self.org_id:
            # Use specified org_id
            try:
                self.config = MaalyPayOrganizationPaymentSystem.objects.select_related(
                    'organization'
                ).get(organization_id=self.org_id)
                self.org = self.config.organization

                print(f"✅ Selected organization: {self.org.title} (ID: {self.org.id})")
                print(f"   Merchant ID: {self.config.merchant_id}")
                print(f"   Has bank_info: {bool(self.config.bank_info)}")
                return True

            except MaalyPayOrganizationPaymentSystem.DoesNotExist:
                print(f"❌ Organization {self.org_id} doesn't have MaalyPay configured!")
                return False
        else:
            # Auto-select first available
            orgs = self.list_available_organizations()
            if not orgs:
                return False

            self.org = Organization.objects.get(id=orgs[0]['id'])
            self.config = orgs[0]['config']

            print(f"\n✅ Auto-selected: {self.org.title} (ID: {self.org.id})")
            print(f"   (Use --org-id={self.org.id} to explicitly select this org)")
            return True

    def create_test_transaction(self):
        """Create test transaction using existing org"""
        self.print_header("Creating Test Transaction")

        try:
            # Get USD currency (or first available)
            try:
                currency = Currency.objects.get(code="USD")
            except Currency.DoesNotExist:
                currency = Currency.objects.first()
                print(f"⚠️  USD not found, using {currency.code}")

            # Use organization owner as client
            client = self.org.owner

            # Create transaction
            self.transaction = Transaction.objects.create(
                organization=self.org,
                client=client,
                processed_by=client,
                type=Transaction.ORG_SUBSCRIPTION,
                payment_status=Transaction.IN_PROGRESS,
                is_processed=False,
                original_amount=Decimal("1.00"),  # Small test amount
                final_amount=Decimal("1.00"),
                currency=currency,
            )

            print("✅ Transaction created")
            print(f"   ID: {self.transaction.id}")
            print(f"   Amount: {self.transaction.final_amount} {currency.code}")
            print(f"   Type: {self.transaction.type}")
            print(f"   Client: {client.phone_number}")

            return True

        except Exception as e:
            print(f"❌ Failed to create transaction: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_payment_creation(self):
        """Test payment creation with real or simulated API"""
        self.print_header("Testing Payment Creation")

        merchant_tx_id = MaalyPayService.generate_merchant_tx_id(self.transaction.id)

        # Prepare request data
        request_data = {
            "merchant_tx_id": merchant_tx_id,
            "amount": str(self.transaction.final_amount),
            "currency": self.transaction.currency.code,
            "description": f"Staging test payment for org {self.org.id}",
            "callback_url": f"https://test.apofiz.com/api/v1/transactions/maalypay/result/?tx={self.transaction.id}",
            "customer_email": self.org.owner.email or "test@staging.local",
            "bank_info": self.config.bank_info,
        }

        print("\n📤 Request Data:")
        for key, value in request_data.items():
            if key == "bank_info" and value:
                print(f"   {key}: {value[:20]}...")
            else:
                print(f"   {key}: {value}")

        if self.use_real_api:
            # REAL API CALL
            print("\n⚠️  Making REAL API call to MaalyPay...")

            checkout_url = MaalyPayService.create_payment(
                api_key=self.config.api_key,
                merchant_id=int(self.config.merchant_id) if self.config.merchant_id.isdigit() else 1,
                amount=request_data["amount"],
                currency=request_data["currency"],
                description=request_data["description"],
                merchant_tx_id=merchant_tx_id,
                callback_url=request_data["callback_url"],
                customer_email=request_data["customer_email"],
                bank_info=request_data["bank_info"],
            )

            if checkout_url:
                print("\n✅ REAL Payment created!")
                print(f"   Checkout URL: {checkout_url}")
                print("\n🔗 Open this URL to complete payment:")
                print(f"   {checkout_url}")

                # Save for later status check
                self.transaction.payment_info = {"merchant_tx_id": merchant_tx_id}
                self.transaction.save()

                return True
            else:
                print("\n❌ Payment creation failed!")
                print("   Check logs for details")
                return False

        else:
            # SIMULATION
            checkout_url = f"https://maalyportal.com/api/omerch/payment-page/{merchant_tx_id}"

            print("\n📥 Simulated Response:")
            print(json.dumps({
                "CheckoutUrl": checkout_url
            }, indent=2))

            print("\n✅ Payment creation simulated successfully")
            print("   (Run with --real-api to test with actual MaalyPay API)")

            return True

    def test_status_check(self):
        """Test status checking"""
        self.print_header("Testing Status Check")

        if not self.transaction.payment_info or 'merchant_tx_id' not in self.transaction.payment_info:
            print("⚠️  Skipping - no merchant_tx_id available")
            print("   This test requires a real payment to be created first")
            return True

        merchant_tx_id = self.transaction.payment_info['merchant_tx_id']

        if self.use_real_api:
            print(f"🔍 Checking real status for: {merchant_tx_id}")

            status = MaalyPayService.check_status(
                api_key=self.config.api_key,
                merchant_tx_id=merchant_tx_id
            )

            if status:
                print("\n✅ Status retrieved:")
                print(json.dumps(status, indent=2, default=str))
                return True
            else:
                print("\n⚠️  Status not available yet (payment may not be completed)")
                return True
        else:
            print("ℹ️  Simulation mode - skipping status check")
            print("   Use --real-api to check real payment status")
            return True

    def cleanup_test_transaction(self):
        """Clean up test transaction"""
        self.print_header("Cleanup")

        if self.transaction and self.transaction.payment_status == Transaction.IN_PROGRESS:
            print(f"🗑️  Removing test transaction {self.transaction.id}")
            self.transaction.delete()
            print("✅ Cleanup complete")
        else:
            print("ℹ️  No cleanup needed (transaction was processed or doesn't exist)")

    def run(self):
        """Run the staging test"""
        print("\n" + "🧪" * 40)
        print("MAALYPAY STAGING/DEV TESTING")
        print("🧪" * 40)

        if self.use_real_api:
            print("\n⚠️  MODE: REAL API")
            print("   Will make actual calls to MaalyPay")
        else:
            print("\n📋 MODE: SIMULATION")
            print("   Will simulate API responses")

        # Step 1: Select organization
        if not self.select_organization():
            return False

        # Step 2: Create test transaction
        if not self.create_test_transaction():
            return False

        # Step 3: Test payment creation
        payment_created = self.test_payment_creation()

        # Step 4: Test status check (if real API)
        if payment_created and self.use_real_api:
            input("\n⏸️  Press Enter after completing payment to check status...")
            self.test_status_check()

        # Step 5: Cleanup
        if not self.use_real_api:
            self.cleanup_test_transaction()
        else:
            print("\n⚠️  Keeping transaction for manual verification")
            print(f"   Transaction ID: {self.transaction.id}")

        # Summary
        self.print_header("Test Complete")
        print("\n✅ Staging test finished!")

        if self.use_real_api:
            print("\n📊 Transaction Details:")
            print(f"   ID: {self.transaction.id}")
            print(f"   Status: {self.transaction.payment_status}")
            print("   Checkout URL in logs above")
        else:
            print("\nℹ️  This was a simulation. To test with real API:")
            print(f"   python test_maalypay_staging.py --real-api --org-id={self.org.id}")

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='MaalyPay Staging Testing')
    parser.add_argument('--org-id', type=int, help='Organization ID to test with')
    parser.add_argument('--real-api', action='store_true', help='Use real MaalyPay API')
    parser.add_argument('--list-orgs', action='store_true', help='List available organizations')

    args = parser.parse_args()

    if args.list_orgs:
        tester = MaalyPayStagingTest()
        tester.list_available_organizations()
        return

    tester = MaalyPayStagingTest(
        org_id=args.org_id,
        use_real_api=args.real_api
    )

    success = tester.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
