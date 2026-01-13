import logging
from celery import shared_task
from django.utils import timezone

from messenger_bots.models import (
    BotChat,
    BotMessage,
    BotCreationRequest,
    BotCreationStatus,
    TelegramBot,
    TelegramUserbot,
    WhatsAppBot,
)
from messenger_bots.services import BotFactoryService, TelegramBotService
from messenger_bots.services.assistant import BotAssistantService

logger = logging.getLogger(__name__)

# Number of previous messages to include for context
CHAT_HISTORY_LIMIT = 5


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_telegram_bot_task(self, request_id: int, base_url: str):
    """
    Celery task to create a Telegram bot via BotFather.

    Args:
        request_id: ID of BotCreationRequest
        base_url: Base URL for webhook setup
    """
    logger.info(f"[CELERY_TASK] ====== CREATE_TELEGRAM_BOT_TASK START ======")
    logger.info(f"[CELERY_TASK] request_id={request_id}, base_url={base_url}")
    logger.info(f"[CELERY_TASK] task_id={self.request.id}, retry={self.request.retries}")

    try:
        request = BotCreationRequest.objects.select_related("organization").get(
            id=request_id
        )
        logger.info(f"[CELERY_TASK] Request found: org_id={request.organization_id}, bot_name='{request.bot_name}'")
    except BotCreationRequest.DoesNotExist:
        logger.error(f"[CELERY_TASK] ERROR: BotCreationRequest {request_id} not found")
        return {"success": False, "error": "Request not found"}

    if request.status == BotCreationStatus.COMPLETED:
        logger.info(f"[CELERY_TASK] Request {request_id} already COMPLETED, skipping")
        return {"success": True, "message": "Already completed"}

    logger.info(f"[CELERY_TASK] Current status: {request.status}")

    # Create bot via BotFactory
    logger.info(f"[CELERY_TASK] Calling BotFactoryService.create_bot_sync()...")
    success, result = BotFactoryService.create_bot_sync(request)
    logger.info(f"[CELERY_TASK] BotFactory result: success={success}")

    if not success:
        logger.error(f"[CELERY_TASK] ERROR: Failed to create bot: {result}")

        # Retry if it's a temporary error
        if "rate limit" in result.lower() or "try again" in result.lower():
            logger.info(f"[CELERY_TASK] Temporary error detected, will retry...")
            raise self.retry(exc=Exception(result))

        logger.error(f"[CELERY_TASK] ====== CREATE_TELEGRAM_BOT_TASK FAILED ======")
        return {"success": False, "error": result}

    # Bot created successfully, now setup webhook
    bot_token = result
    logger.info(f"[CELERY_TASK] Bot created! Token: {bot_token[:20]}...")

    try:
        # Create TelegramBot record
        logger.info(f"[CELERY_TASK] Creating TelegramBot record...")
        telegram_bot, created = TelegramBot.objects.update_or_create(
            organization=request.organization,
            defaults={
                "bot_token": bot_token,
                "bot_username": request.bot_username,
                "is_active": True,
            },
        )
        logger.info(f"[CELERY_TASK] TelegramBot {'created' if created else 'updated'}: id={telegram_bot.id}")

        # Setup webhook
        logger.info(f"[CELERY_TASK] Setting up webhook...")
        service = TelegramBotService(telegram_bot)
        bot_info = service.get_me()

        if bot_info:
            logger.info(f"[CELERY_TASK] Bot info received: @{bot_info.get('username')}")
            webhook_url = f"{base_url}/api/v1/messenger-bots/telegram/webhook/{request.organization.id}/"
            logger.info(f"[CELERY_TASK] Setting webhook to: {webhook_url}")
            webhook_success = service.set_webhook(webhook_url)

            if not webhook_success:
                logger.warning(f"[CELERY_TASK] WARNING: Failed to set webhook for @{request.bot_username}")
            else:
                logger.info(f"[CELERY_TASK] Webhook set successfully!")
        else:
            logger.warning(f"[CELERY_TASK] WARNING: Could not get bot info (getMe failed)")

        logger.info(f"[CELERY_TASK] ====== CREATE_TELEGRAM_BOT_TASK SUCCESS ======")
        logger.info(f"[CELERY_TASK] Bot @{request.bot_username} created and configured for org {request.organization_id}")

        return {
            "success": True,
            "bot_username": request.bot_username,
            "bot_token": bot_token[:20] + "...",  # Truncate for security
        }

    except Exception as e:
        logger.error(f"[CELERY_TASK] ERROR setting up bot after creation: {e}", exc_info=True)
        return {
            "success": True,
            "bot_username": request.bot_username,
            "warning": f"Bot created but webhook setup failed: {e}",
        }


@shared_task
def reset_userbot_daily_counters():
    """
    Reset daily bot creation counters for all userbots.
    Should be scheduled to run at midnight.
    """
    updated = TelegramUserbot.objects.filter(
        bots_created_today__gt=0
    ).update(bots_created_today=0)

    logger.info(f"Reset daily counters for {updated} userbots")
    return {"reset_count": updated}


@shared_task
def check_pending_bot_requests():
    """
    Check for pending bot creation requests and process them.
    Useful as a fallback if a task was lost.
    """
    pending_requests = BotCreationRequest.objects.filter(
        status=BotCreationStatus.PENDING,
        created_at__lt=timezone.now() - timezone.timedelta(minutes=5),
    ).select_related("organization")[:10]

    for request in pending_requests:
        logger.info(f"Processing stale pending request {request.id}")
        # Get base_url from organization or use default
        base_url = "https://apofiz.com"  # Default, should be configured
        create_telegram_bot_task.delay(request.id, base_url)

    return {"processed": len(pending_requests)}


# ============== WhatsApp WAHA Tasks ==============

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_whatsapp_message_task(
    self,
    whatsapp_bot_id: int,
    chat_id: int,
    message_text: str,
):
    """
    Process incoming WhatsApp message with AI assistant.

    Args:
        whatsapp_bot_id: ID of WhatsAppBot
        chat_id: ID of BotChat
        message_text: Incoming message text
    """
    logger.info(f"[WA_TASK] ====== PROCESS_WHATSAPP_MESSAGE START ======")
    logger.info(f"[WA_TASK] whatsapp_bot_id={whatsapp_bot_id}, chat_id={chat_id}")
    logger.info(f"[WA_TASK] message='{message_text[:100]}...'")

    try:
        whatsapp_bot = WhatsAppBot.objects.select_related("organization").get(
            id=whatsapp_bot_id
        )
        chat = BotChat.objects.select_related("organization").get(id=chat_id)
        logger.info(f"[WA_TASK] Bot and chat found: org_id={whatsapp_bot.organization_id}, phone={chat.platform_chat_id}")
    except (WhatsAppBot.DoesNotExist, BotChat.DoesNotExist) as e:
        logger.error(f"[WA_TASK] ERROR: Bot or chat not found: {e}")
        return {"success": False, "error": str(e)}

    # Get chat history for context
    chat_history = _get_whatsapp_chat_history(chat)
    logger.debug(f"[WA_TASK] Chat history: {len(chat_history)} messages")

    # Determine user language (default to Russian for WhatsApp)
    user_language = "ru"

    # Get AI response
    logger.info(f"[WA_TASK] Requesting AI response...")
    try:
        response_text = BotAssistantService.get_response(
            organization=whatsapp_bot.organization,
            question=message_text,
            chat_history=chat_history,
            user_language=user_language,
        )
        logger.info(f"[WA_TASK] AI response: '{response_text[:100]}...'")
    except Exception as e:
        logger.error(f"[WA_TASK] ERROR: AI service error: {e}", exc_info=True)
        response_text = BotAssistantService._get_message("error", user_language)

    # Send response via WAHA
    logger.info(f"[WA_TASK] Sending response via WAHA...")
    try:
        from messenger_bots.services.whatsapp import WhatsAppServiceFactory
        from messenger_bots.services.whatsapp.base import WhatsAppMessage

        service = WhatsAppServiceFactory.get_service(whatsapp_bot)

        message = WhatsAppMessage(
            to=chat.platform_chat_id,
            text=response_text,
        )
        result = service.send_message(message)

        if result.success:
            # Save assistant response
            BotMessage.objects.create(
                chat=chat,
                sender=BotMessage.ASSISTANT,
                text=response_text,
                platform_message_id=result.message_id,
            )
            logger.info(f"[WA_TASK] ====== PROCESS_WHATSAPP_MESSAGE SUCCESS ======")
            logger.info(f"[WA_TASK] Response sent to {chat.platform_chat_id}, msg_id={result.message_id}")
            return {
                "success": True,
                "message_id": result.message_id,
            }
        else:
            logger.error(f"[WA_TASK] ERROR: Failed to send response: {result.error}")
            # Save error in bot
            whatsapp_bot.last_error = result.error
            whatsapp_bot.save(update_fields=["last_error"])
            return {
                "success": False,
                "error": result.error,
            }

    except Exception as e:
        logger.error(f"[WA_TASK] ERROR: WhatsApp send error: {e}", exc_info=True)
        raise self.retry(exc=e)


def _get_whatsapp_chat_history(chat: BotChat) -> list:
    """Get recent chat history for AI context."""
    messages = chat.messages.order_by("-created_at")[:CHAT_HISTORY_LIMIT]

    history = []
    for msg in reversed(messages):
        history.append({
            "role": "user" if msg.sender == BotMessage.USER else "assistant",
            "content": msg.text,
        })

    return history


@shared_task
def check_waha_session_health():
    """
    Periodically check WAHA session health for all active bots.
    Should be scheduled to run every 5-10 minutes.
    """
    from messenger_bots.models import WhatsAppProvider, WhatsAppSessionStatus
    from messenger_bots.services.whatsapp import WhatsAppServiceFactory

    waha_bots = WhatsAppBot.objects.filter(
        provider=WhatsAppProvider.WAHA,
        is_active=True,
    )

    results = []
    for bot in waha_bots:
        try:
            service = WhatsAppServiceFactory.get_service(bot)
            is_healthy = service.is_healthy()

            if is_healthy:
                # Update status if it was marked as failed/disconnected
                if bot.session_status in [
                    WhatsAppSessionStatus.FAILED,
                    WhatsAppSessionStatus.DISCONNECTED,
                ]:
                    bot.session_status = WhatsAppSessionStatus.AUTHENTICATED
                    bot.last_error = None
                    bot.save(update_fields=["session_status", "last_error"])

                results.append({
                    "org_id": bot.organization_id,
                    "status": "healthy",
                })
            else:
                # Mark as disconnected if unhealthy
                if bot.session_status == WhatsAppSessionStatus.AUTHENTICATED:
                    bot.session_status = WhatsAppSessionStatus.DISCONNECTED
                    bot.last_error = "Session health check failed"
                    bot.save(update_fields=["session_status", "last_error"])

                results.append({
                    "org_id": bot.organization_id,
                    "status": "unhealthy",
                })

        except Exception as e:
            logger.error(f"WAHA health check failed for org {bot.organization_id}: {e}")
            results.append({
                "org_id": bot.organization_id,
                "status": "error",
                "error": str(e),
            })

    logger.info(f"WAHA health check completed: {len(results)} bots checked")
    return {"checked": len(results), "results": results}


@shared_task
def sync_waha_session_status():
    """
    Sync WAHA session status from WAHA API to database.
    Handles cases where webhook wasn't received.
    """
    from messenger_bots.models import WhatsAppProvider, WhatsAppSessionStatus
    from messenger_bots.services.whatsapp import WhatsAppServiceFactory

    waha_bots = WhatsAppBot.objects.filter(
        provider=WhatsAppProvider.WAHA,
        is_active=True,
    )

    for bot in waha_bots:
        try:
            service = WhatsAppServiceFactory.get_service(bot)
            connection_status = service.check_connection()

            waha_status = connection_status.get("status", "UNKNOWN")

            # Map WAHA status to our status
            status_mapping = {
                "STARTING": WhatsAppSessionStatus.PENDING,
                "SCAN_QR_CODE": WhatsAppSessionStatus.SCAN_QR,
                "WORKING": WhatsAppSessionStatus.AUTHENTICATED,
                "STOPPED": WhatsAppSessionStatus.DISCONNECTED,
                "FAILED": WhatsAppSessionStatus.FAILED,
            }

            new_status = status_mapping.get(waha_status)
            if new_status and new_status != bot.session_status:
                logger.info(
                    f"Syncing WAHA status for org {bot.organization_id}: "
                    f"{bot.session_status} -> {new_status}"
                )
                bot.session_status = new_status
                bot.save(update_fields=["session_status"])

        except Exception as e:
            logger.error(f"WAHA status sync failed for org {bot.organization_id}: {e}")
