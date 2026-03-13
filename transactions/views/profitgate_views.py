import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from transactions.models import Transaction
from organizations.models import ProfitgateIntegration
from organizations.services.profitgate_service import ProfitgateService

logger = logging.getLogger(__name__)

class ProfitgateInitPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, transaction_id):
        transaction = get_object_or_404(Transaction, id=transaction_id, client=request.user)
        integration = get_object_or_404(
            ProfitgateIntegration, 
            organization=transaction.organization, 
            is_active=True
        )
        if not integration.currencies.filter(id=transaction.currency_id).exists():
            return Response({"error": "Валюта не поддерживается"}, status=400)

        service = ProfitgateService(integration)
        finish_url = request.build_absolute_view_uri('/payment/success/')
        notification_url = request.build_absolute_uri('/api/v1/transactions/webhooks/profitgate/')
        
        try:
            redirect_url = service.create_redirect_payment(
                transaction, finish_url, notification_url
            )
            return Response({"redirect_url": redirect_url})
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class ProfitgateWebhookAPIView(APIView):
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        data = request.data
        order_id = data.get("order")
        tx_status = data.get("status")
        merchant_id = data.get("merchant_id")
        
        if not order_id or not merchant_id:
            return Response({"error": "Bad request"}, status=400)

        try:
            transaction = Transaction.objects.get(id=order_id)
            integration = ProfitgateIntegration.objects.get(merchant_id=merchant_id)
            service = ProfitgateService(integration)
            if not service.verify_webhook(request.path, data):
                logger.warning(f"Profitgate Fake Webhook attempt for order {order_id}")
                return Response({"error": "Invalid signature"}, status=403)
            if tx_status == "complete":
                transaction.status = "SUCCESS" 
            elif tx_status == "partial_complete":
                transaction.status = "PARTIAL" 
            elif tx_status == "failed":
                transaction.status = "FAILED"
                
            transaction.save()
            return Response({"status": "ok"}, status=200)
            
        except Exception as e:
            logger.exception("Profitgate webhook error")
            return Response({"error": "Internal Error"}, status=500)