import json
import base64
import hashlib
import hmac
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ProfitgateService:
    BASE_URL = "https://secure-api.profitgate.pro"

    def __init__(self, integration):
        self.integration = integration

    def _base64url_encode(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

    def generate_signature(self, path, payload, method="POST"):
        payload_copy = payload.copy()
        payload_copy.pop('signature', None)
        sorted_payload = {str(k): str(v) for k, v in sorted(payload_copy.items())}
        
        header_json = json.dumps({"alg": "HS256"}, separators=(',', ':'))
        payload_json = json.dumps({"PATH": path, method: sorted_payload}, separators=(',', ':'))
        
        head_input = self._base64url_encode(header_json)
        payload_input = self._base64url_encode(payload_json)
        
        signature_input = f"{head_input}.{payload_input}"
        
        signature = hmac.new(
            self.integration.api_secret.encode('utf-8'),
            signature_input.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return self._base64url_encode(signature)

    def create_redirect_payment(self, transaction, finish_url=None, notification_url=None):
        path = "/init"
        
        payload = {
            "amount": str(transaction.amount),
            "order": str(transaction.id),
            "merchant_id": str(self.integration.merchant_id),
            "endpoint_id": str(self.integration.endpoint_id),
            "currency": str(transaction.currency),
            "customer": str(transaction.user.id),
        }
        if finish_url: payload["finish_url"] = finish_url
        if notification_url: payload["notification_url"] = notification_url

        payload["signature"] = self.generate_signature(path, payload)

        response = requests.post(f"{self.BASE_URL}{path}", json=payload)
        data = response.json()

        if response.status_code == 200 and data.get("status") == "redirect":
            return data.get("url")
        
        logger.error(f"Profitgate redirect error: {data}")
        raise ValueError(f"Payment init failed: {data}")

    def create_h2h_payment(self, transaction, card_data):
        path = "/init" 
        payload = {
            "amount": str(transaction.amount),
            "order": str(transaction.id),
            "merchant_id": str(self.integration.merchant_id),
            "endpoint_id": str(self.integration.endpoint_id),
            "currency": str(transaction.currency),
            "customer": str(transaction.user.id),
            "pan": str(card_data['pan']),
            "expire_month": str(card_data['expire_month']),
            "expire_year": str(card_data['expire_year']),
            "cvc": str(card_data['cvc']),
            "first_name": str(card_data['first_name']),
            "last_name": str(card_data['last_name']),
        }
        
        payload["signature"] = self.generate_signature(path, payload)
        
        response = requests.post(f"{self.BASE_URL}{path}", json=payload)
        return response.json()

    def process_withdrawal(self, withdrawal_id, amount, currency, customer_id, pan):
        path = "/withdrawal"
        payload = {
            "merchant_id": str(self.integration.merchant_id),
            "endpoint_id": str(self.integration.endpoint_id),
            "order": str(withdrawal_id),
            "pan": str(pan),
            "amount": str(amount),
            "currency": str(currency),
            "customer": str(customer_id),
        }
        payload["signature"] = self.generate_signature(path, payload)
        
        response = requests.post(f"{self.BASE_URL}{path}", json=payload)
        return response.json()

    def verify_webhook(self, path, request_data):
        received_signature = request_data.get("signature")
        if not received_signature:
            return False
            
        expected_signature = self.generate_signature(path, request_data)
        return hmac.compare_digest(received_signature, expected_signature)