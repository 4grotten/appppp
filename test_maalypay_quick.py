#!/usr/bin/env python
"""
Quick MaalyPay test - create payment and check status
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.base")
django.setup()

from decimal import Decimal
from common.models import Currency
from organizations.models import MaalyPayOrganizationPaymentSystem
from organizations.services.maalypay_service import MaalyPayService
from transactions.models import Transaction

def main():
    print("\n" + "="*80)
    print("QUICK MAALYPAY TEST")
    print("="*80)

    # Find MaalyPay config
    try:
        config = MaalyPayOrganizationPaymentSystem.objects.select_related('organization').get(merchant_id='172')
        org = config.organization
        print(f"\n✅ Found organization: {org.title} (ID: {org.id})")
        print(f"   Merchant ID: {config.merchant_id}")
    except MaalyPayOrganizationPaymentSystem.DoesNotExist:
        print("\n❌ No MaalyPay config found for merchant 172")
        return 1

    # Get currency
    try:
        currency = Currency.objects.get(code="USD")
    except Currency.DoesNotExist:
        currency = Currency.objects.first()
        print(f"⚠️  USD not found, using {currency.code}")

    # Create transaction with ACCEPTED status (not IN_PROGRESS!)
    client = org.owner
    transaction = Transaction.objects.create(
        organization=org,
        client=client,
        processed_by=client,
        type=Transaction.ORG_SUBSCRIPTION,
        payment_status=Transaction.ACCEPTED,  # IMPORTANT: Must be ACCEPTED
        is_processed=False,
        original_amount=Decimal("1.00"),
        final_amount=Decimal("1.00"),
        currency=currency,
    )

    print(f"\n✅ Transaction created: ID={transaction.id}")
    print(f"   Status: {transaction.payment_status}")
    print(f"   Is Processed: {transaction.is_processed}")

    # Create payment
    merchant_tx_id = MaalyPayService.generate_merchant_tx_id(transaction.id)

    print(f"\n📤 Creating MaalyPay payment...")
    print(f"   Merchant TX ID: {merchant_tx_id}")

    checkout_url = MaalyPayService.create_payment(
        api_key=config.api_key,
        merchant_id=int(config.merchant_id),
        amount="1.00",
        currency="USD",
        description="Quick test payment",
        merchant_tx_id=merchant_tx_id,
        callback_url=f"https://test.apofiz.com/transactions/maalypay/result/?tx={transaction.id}",
        customer_email=client.email or "test@test.com",
        bank_info=config.bank_info,
    )

    if checkout_url:
        print(f"\n✅ Payment created!")
        print(f"   Checkout URL: {checkout_url}")

        # Check status immediately
        print(f"\n🔍 Checking payment status immediately...")
        status = MaalyPayService.check_status(config.api_key, merchant_tx_id)

        if status:
            print(f"\n📊 MaalyPay API Response:")
            print(f"   Status: {status.get('status')} (type: {type(status.get('status')).__name__})")
            print(f"   Fiat Amount: {status.get('fiatAmount')}")
            print(f"   Filled Amount: {status.get('filledAmount')}")
            print(f"   TX Hash: {status.get('txHash')}")
            print(f"   Network: {status.get('network')}")
            print(f"   Asset: {status.get('asset')}")
        else:
            print("   ⚠️  No status data returned")

        # Reload transaction from DB
        transaction.refresh_from_db()
        print(f"\n📊 Transaction Status After Check:")
        print(f"   Payment Status: {transaction.payment_status}")
        print(f"   Is Processed: {transaction.is_processed}")

        if transaction.is_processed:
            print("\n⚠️  WARNING: Transaction was processed WITHOUT user payment!")
            print("   This means MaalyPay API returned status: true immediately")
        else:
            print("\n✅ Transaction is NOT processed yet (correct behavior)")

        print(f"\n🔗 Open this URL to pay:")
        print(f"   {checkout_url}")

        print(f"\n💡 To check transaction later, run:")
        print(f"   Transaction.objects.get(id={transaction.id})")

        return 0
    else:
        print("\n❌ Payment creation failed!")
        transaction.delete()
        return 1

if __name__ == "__main__":
    sys.exit(main())
