import asyncio
import logging

from celery import shared_task
from django.utils import timezone

from messenger_bots.models import (
    BotChat,
    BotCreationRequest,
    BotCreationStatus,
    BotMessage,
    TelegramBot,
    TelegramUserbot,
    WhatsAppBot,
)
from messenger_bots.services import BotFactoryService, TelegramBotService
from messenger_bots.services.assistant import BotAssistantService

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(bind=True, time_limit=120, soft_time_limit=100)
def userbot_send_code_task(self, userbot_id: int):
    logger.info(f"[USERBOT_TASK] send_code started for userbot_id={userbot_id}")

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.send_code())

    logger.info(f"[USERBOT_TASK] send_code result: {result}")
    return result


@shared_task(bind=True, time_limit=120, soft_time_limit=100)
def userbot_verify_code_task(self, userbot_id: int, code: str):
    logger.info(f"[USERBOT_TASK] verify_code started for userbot_id={userbot_id}")

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.verify_code(code))

    logger.info(f"[USERBOT_TASK] verify_code result: {result}")
    return result


@shared_task(bind=True, time_limit=120, soft_time_limit=100)
def userbot_verify_2fa_task(self, userbot_id: int, password: str):
    logger.info(f"[USERBOT_TASK] verify_2fa started for userbot_id={userbot_id}")

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.verify_2fa(password))

    logger.info(f"[USERBOT_TASK] verify_2fa result: {result}")
    return result


@shared_task(bind=True, time_limit=60, soft_time_limit=50)
def userbot_check_connection_task(self, userbot_id: int):
    logger.info(f"[USERBOT_TASK] check_connection started for userbot_id={userbot_id}")

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.check_connection())

    logger.info(f"[USERBOT_TASK] check_connection result: {result}")
    return result


@shared_task(bind=True, time_limit=60, soft_time_limit=50)
def userbot_logout_task(self, userbot_id: int):
    logger.info(f"[USERBOT_TASK] logout started for userbot_id={userbot_id}")

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.logout())

    logger.info(f"[USERBOT_TASK] logout result: {result}")
    return result


@shared_task(bind=True, time_limit=60, soft_time_limit=50)
def userbot_get_dialogs_task(self, userbot_id: int, limit: int = 30):
    logger.info(f"[USERBOT_TASK] get_dialogs started for userbot_id={userbot_id}")

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.get_dialogs(limit=limit))

    logger.info(
        f"[USERBOT_TASK] get_dialogs result: found {len(result.get('dialogs', []))} dialogs"
    )
    return result


@shared_task(bind=True, time_limit=60, soft_time_limit=50)
def userbot_send_test_message_task(self, userbot_id: int, chat: str, message: str):
    logger.info(f"[USERBOT_TASK] send_test_message started for userbot_id={userbot_id}")

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.send_test_message(chat, message))

    logger.info(f"[USERBOT_TASK] send_test_message result: {result}")
    return result


CHAT_HISTORY_LIMIT = 5


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_telegram_bot_task(self, request_id: int, base_url: str):
    logger.info("[CELERY_TASK] ====== CREATE_TELEGRAM_BOT_TASK START ======")
    logger.info(f"[CELERY_TASK] request_id={request_id}, base_url={base_url}")
    logger.info(
        f"[CELERY_TASK] task_id={self.request.id}, retry={self.request.retries}"
    )

    try:
        request = BotCreationRequest.objects.select_related("organization").get(
            id=request_id
        )
        logger.info(
            f"[CELERY_TASK] Request found: org_id={request.organization.id}, bot_name='{request.bot_name}'"
        )
    except BotCreationRequest.DoesNotExist:
        logger.error(f"[CELERY_TASK] ERROR: BotCreationRequest {request_id} not found")
        return {"success": False, "error": "Request not found"}

    if request.status == BotCreationStatus.COMPLETED:
        logger.info(f"[CELERY_TASK] Request {request_id} already COMPLETED, skipping")
        return {"success": True, "message": "Already completed"}

    logger.info(f"[CELERY_TASK] Current status: {request.status}")

    logger.info("[CELERY_TASK] Calling BotFactoryService.create_bot_sync()...")
    success, result = BotFactoryService.create_bot_sync(request)
    logger.info(f"[CELERY_TASK] BotFactory result: success={success}")

    if not success:
        logger.error(f"[CELERY_TASK] ERROR: Failed to create bot: {result}")

        if "rate limit" in result.lower() or "try again" in result.lower():
            logger.info("[CELERY_TASK] Temporary error detected, will retry...")
            raise self.retry(exc=Exception(result))

        logger.error("[CELERY_TASK] ====== CREATE_TELEGRAM_BOT_TASK FAILED ======")
        return {"success": False, "error": result}

    bot_token = result
    logger.info(f"[CELERY_TASK] Bot created! Token: {bot_token[:20]}...")

    try:
        logger.info("[CELERY_TASK] Creating TelegramBot record...")
        telegram_bot, created = TelegramBot.objects.update_or_create(
            organization=request.organization,
            defaults={
                "bot_token": bot_token,
                "bot_username": request.bot_username,
                "is_active": True,
            },
        )
        logger.info(
            f"[CELERY_TASK] TelegramBot {'created' if created else 'updated'}: id={telegram_bot.id}"
        )

        logger.info("[CELERY_TASK] Setting up webhook...")
        service = TelegramBotService(telegram_bot)
        bot_info = service.get_me()

        if bot_info:
            logger.info(f"[CELERY_TASK] Bot info received: @{bot_info.get('username')}")
            webhook_url = f"{base_url}/api/v1/messenger-bots/telegram/webhook/{request.organization.id}/"
            logger.info(f"[CELERY_TASK] Setting webhook to: {webhook_url}")
            webhook_success = service.set_webhook(webhook_url)

            if not webhook_success:
                logger.warning(
                    f"[CELERY_TASK] WARNING: Failed to set webhook for @{request.bot_username}"
                )
            else:
                logger.info("[CELERY_TASK] Webhook set successfully!")
        else:
            logger.warning(
                "[CELERY_TASK] WARNING: Could not get bot info (getMe failed)"
            )

        logger.info("[CELERY_TASK] ====== CREATE_TELEGRAM_BOT_TASK SUCCESS ======")
        logger.info(
            f"[CELERY_TASK] Bot @{request.bot_username} created and configured for org {request.organization.id}"
        )

        return {
            "success": True,
            "bot_username": request.bot_username,
            "bot_token": bot_token[:20] + "...",
        }

    except Exception as e:
        logger.error(
            f"[CELERY_TASK] ERROR setting up bot after creation: {e}", exc_info=True
        )
        return {
            "success": True,
            "bot_username": request.bot_username,
            "warning": f"Bot created but webhook setup failed: {e}",
        }


@shared_task
def reset_userbot_daily_counters():
    updated = TelegramUserbot.objects.filter(bots_created_today__gt=0).update(
        bots_created_today=0
    )

    logger.info(f"Reset daily counters for {updated} userbots")
    return {"reset_count": updated}


@shared_task
def check_pending_bot_requests():
    pending_requests = BotCreationRequest.objects.filter(
        status=BotCreationStatus.PENDING,
        created_at__lt=timezone.now() - timezone.timedelta(minutes=5),
    ).select_related("organization")[:10]

    for request in pending_requests:
        logger.info(f"Processing stale pending request {request.id}")
        base_url = "https://apofiz.com"  # Default, should be configured
        create_telegram_bot_task.delay(request.id, base_url)

    return {"processed": len(pending_requests)}


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_whatsapp_message_task(
    self,
    whatsapp_bot_id: int,
    chat_id: int,
    message_text: str,
):
    logger.info("[WA_TASK] ====== PROCESS_WHATSAPP_MESSAGE START ======")
    logger.info(f"[WA_TASK] whatsapp_bot_id={whatsapp_bot_id}, chat_id={chat_id}")
    logger.info(f"[WA_TASK] message='{message_text[:100]}...'")

    try:
        whatsapp_bot = WhatsAppBot.objects.select_related("organization").get(
            id=whatsapp_bot_id
        )
        chat = BotChat.objects.select_related("organization").get(id=chat_id)
        logger.info(
            f"[WA_TASK] Bot and chat found: org_id={whatsapp_bot.organization.id}, phone={chat.platform_chat_id}"
        )
    except (WhatsAppBot.DoesNotExist, BotChat.DoesNotExist) as e:
        logger.error(f"[WA_TASK] ERROR: Bot or chat not found: {e}")
        return {"success": False, "error": str(e)}

    chat_history = _get_whatsapp_chat_history(chat)
    logger.debug(f"[WA_TASK] Chat history: {len(chat_history)} messages")

    user_language = "ru"

    logger.info("[WA_TASK] Requesting AI response...")
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

    logger.info("[WA_TASK] Sending response via WAHA...")
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
            BotMessage.objects.create(
                chat=chat,
                sender=BotMessage.ASSISTANT,
                text=response_text,
                platform_message_id=result.message_id,
            )
            logger.info("[WA_TASK] ====== PROCESS_WHATSAPP_MESSAGE SUCCESS ======")
            logger.info(
                f"[WA_TASK] Response sent to {chat.platform_chat_id}, msg_id={result.message_id}"
            )
            return {
                "success": True,
                "message_id": result.message_id,
            }
        else:
            logger.error(f"[WA_TASK] ERROR: Failed to send response: {result.error}")
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
    messages = chat.messages.order_by("-created_at")[:CHAT_HISTORY_LIMIT]

    history = []
    for msg in reversed(messages):
        history.append(
            {
                "role": "user" if msg.sender == BotMessage.USER else "assistant",
                "content": msg.text,
            }
        )

    return history


@shared_task
def check_waha_session_health():
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
                if bot.session_status in [
                    WhatsAppSessionStatus.FAILED,
                    WhatsAppSessionStatus.DISCONNECTED,
                ]:
                    bot.session_status = WhatsAppSessionStatus.AUTHENTICATED
                    bot.last_error = None
                    bot.save(update_fields=["session_status", "last_error"])

                results.append(
                    {
                        "org_id": bot.organization.id,
                        "status": "healthy",
                    }
                )
            else:
                if bot.session_status == WhatsAppSessionStatus.AUTHENTICATED:
                    bot.session_status = WhatsAppSessionStatus.DISCONNECTED
                    bot.last_error = "Session health check failed"
                    bot.save(update_fields=["session_status", "last_error"])

                results.append(
                    {
                        "org_id": bot.organization.id,
                        "status": "unhealthy",
                    }
                )

        except Exception as e:
            logger.error(f"WAHA health check failed for org {bot.organization.id}: {e}")
            results.append(
                {
                    "org_id": bot.organization.id,
                    "status": "error",
                    "error": str(e),
                }
            )

    logger.info(f"WAHA health check completed: {len(results)} bots checked")
    return {"checked": len(results), "results": results}


@shared_task
def sync_waha_session_status():
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
                    f"Syncing WAHA status for org {bot.organization.id}: "
                    f"{bot.session_status} -> {new_status}"
                )
                bot.session_status = new_status
                bot.save(update_fields=["session_status"])

        except Exception as e:
            logger.error(f"WAHA status sync failed for org {bot.organization.id}: {e}")
