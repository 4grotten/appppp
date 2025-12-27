"""
Quick debug script to check MaalyPay status for transaction 7724
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.base")
django.setup()

import json
from organizations.models import MaalyPayOrganizationPaymentSystem
from organizations.services.maalypay_service import MaalyPayService

# Get config
config = MaalyPayOrganizationPaymentSystem.objects.get(organization_id=1243)

print("=" * 80)
print("MAALYPAY STATUS CHECK FOR TRANSACTION 7724")
print("=" * 80)
print()
print(f"Organization: {config.organization.title}")
print(f"Merchant ID: {config.merchant_id}")
print(f"merchant_tx_id: apofiz-7724")
print()

# Check status
print("Checking status from MaalyPay API...")
print()

status = MaalyPayService.check_status(
    api_key=config.api_key,
    merchant_tx_id='apofiz-7724'
)

if status:
    print("✅ Status retrieved successfully:")
    print()
    print(json.dumps(status, indent=2, default=str))
    print()
    print("=" * 80)
    print("ANALYSIS:")
    print("=" * 80)
    print(f"Status value: {status.get('status')} (type: {type(status.get('status')).__name__})")
    print(f"Filled Amount: {status.get('filledAmount')}")
    print(f"Requested Amount: {status.get('fiatAmount')}")
    print(f"Has txHash: {bool(status.get('txHash'))}")
    if status.get('txHash'):
        print(f"txHash: {status.get('txHash')}")
        print(f"Network: {status.get('network')}")
        print(f"Asset: {status.get('asset')}")
        print(f"Blockchain Explorer: {status.get('txLink')}")
    print()

    # Check if payment should be considered paid
    is_paid = status.get('status') is True
    print(f"Is Paid (according to API): {is_paid}")

    if not is_paid:
        print()
        print("⚠️  PAYMENT NOT YET CONFIRMED BY MAALYPAY")
        print("Possible reasons:")
        print("1. MaalyPay is still waiting for blockchain confirmations")
        print("2. MaalyPay indexer hasn't processed the transaction yet")
        print("3. There's a delay in their system")
        print()
        print("Action: Wait for Celery task to retry, or contact MaalyPay support")
    else:
        print()
        print("✅ PAYMENT CONFIRMED!")
        print("The Celery task should update the transaction on next run")
else:
    print("❌ Failed to retrieve status from MaalyPay API")
    print("Check logs for details")
