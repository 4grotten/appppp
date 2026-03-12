import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from transactions.models import Transaction
from organizations.models import ProfitgateIntegration
from organizations.services.profitgate_service import ProfitgateService

logger = logging.getLogger(__name__)

class ProfitgateWebhookAPIView(APIView):
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            order_id = data.get("order")
            tx_status = data.get("status")
            merchant_id = data.get("merchant_id")
            
            if not order_id or not merchant_id:
                return Response({"error": "Bad payload"}, status=status.HTTP_400_BAD_REQUEST)
            transaction = Transaction.objects.get(id=order_id) 
            integration = ProfitgateIntegration.objects.get(merchant_id=merchant_id, is_active=True)
            service = ProfitgateService(integration)
            if not service.verify_webhook(request.path, data):
                logger.warning(f"Profitgate invalid signature for order {order_id}")
                return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
            if tx_status == "complete":
                transaction.status = "SUCCESS"
            elif tx_status == "partial_complete":
                transaction.status = "PARTIAL" 
            elif tx_status == "failed":
                transaction.status = "FAILED"
            transaction.save()
            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        except Transaction.DoesNotExist:
            logger.error("Profitgate webhook: Transaction not found")
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        except ProfitgateIntegration.DoesNotExist:
            logger.error("Profitgate webhook: Integration not found")
            return Response({"error": "Integration not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Profitgate webhook unhandled error")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)