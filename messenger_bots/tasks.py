import asyncio
import logging
import time

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
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


def _send_ws_notification(bot_message: BotMessage, bot_chat: BotChat) -> None:
    """Send WebSocket notification for new bot message."""
    from shop.serializers.comment_serializers import BotMessageSerializer

    try:
        linked_chat = getattr(bot_chat, 'linked_chat', None)
        if not linked_chat:
            return

        chat_group_name = f"chat_{linked_chat.id}"
        serialized_data = BotMessageSerializer(bot_message).data

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                chat_group_name,
                {"type": "chat_message", "message": serialized_data}
            )
    except Exception as e:
        logger.error(f"[WS_NOTIFICATION] Error: {e}", exc_info=True)


def _run_async(coro):
    """Run async coroutine in synchronous Celery task context.

    Uses asyncio.run() which:
    - Creates a new event loop for the coroutine
    - Runs the coroutine to completion
    - Closes the event loop

    This is the recommended approach for running async code in sync context
    when each call is independent (like Celery tasks). For frequent calls,
    consider using a thread-local event loop instead.

    Note: This pattern is correct for userbot auth operations which are
    infrequent (once per userbot setup).
    """
    return asyncio.run(coro)


@shared_task(time_limit=120, soft_time_limit=100, ignore_result=False)
def userbot_send_code_task(userbot_id: int):
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


@shared_task(time_limit=120, soft_time_limit=100, ignore_result=False)
def userbot_qr_login_start_task(userbot_id: int, force_dc: int = None):
    """
    Start QR code login - returns QR URL to display.

    Args:
        userbot_id: ID of the TelegramUserbot to authenticate
        force_dc: Force specific datacenter (1-5):
            - DC1: Test (Miami)
            - DC2: Europe (Netherlands) - recommended for EU/CIS
            - DC3: USA (Miami)
            - DC4: Europe (Netherlands, files)
            - DC5: Asia (Singapore) - recommended for UAE/Asia
    """
    logger.info(
        f"[USERBOT_TASK] qr_login_start started for userbot_id={userbot_id}, force_dc={force_dc}"
    )

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.qr_login_start(force_dc=force_dc))

    logger.info(f"[USERBOT_TASK] qr_login_start result: {result}")
    return result


@shared_task(time_limit=60, soft_time_limit=50, ignore_result=False)
def userbot_qr_login_check_task(userbot_id: int):
    """Check if user has scanned QR code."""
    logger.info(f"[USERBOT_TASK] qr_login_check started for userbot_id={userbot_id}")

    try:
        userbot = TelegramUserbot.objects.get(id=userbot_id)
    except TelegramUserbot.DoesNotExist:
        logger.error(f"[USERBOT_TASK] Userbot {userbot_id} not found")
        return {"success": False, "error": "Userbot not found"}

    from messenger_bots.services.bot_factory import UserbotAuthService

    service = UserbotAuthService(userbot)
    result = _run_async(service.qr_login_check())

    logger.info(f"[USERBOT_TASK] qr_login_check result: {result}")
    return result


@shared_task(time_limit=120, soft_time_limit=100, ignore_result=False)
def userbot_verify_code_task(userbot_id: int, code: str):
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


@shared_task(time_limit=120, soft_time_limit=100, ignore_result=False)
def userbot_verify_2fa_task(userbot_id: int, password: str):
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


@shared_task(time_limit=60, soft_time_limit=50, ignore_result=False)
def userbot_check_connection_task(userbot_id: int):
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


@shared_task(time_limit=60, soft_time_limit=50, ignore_result=False)
def userbot_logout_task(userbot_id: int):
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


@shared_task(time_limit=60, soft_time_limit=50, ignore_result=False)
def userbot_get_dialogs_task(userbot_id: int, limit: int = 30):
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


@shared_task(time_limit=60, soft_time_limit=50, ignore_result=False)
def userbot_send_test_message_task(userbot_id: int, chat: str, message: str):
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


@shared_task(time_limit=120, soft_time_limit=100, ignore_result=False)
def userbot_set_bot_photo_task(bot_username: str, photo_content_b64: str, content_type: str = "image/jpeg"):
    """
    Set bot profile photo via BotFather using userbot.

    This is the only way to change bot's profile photo programmatically
    since Telegram Bot API doesn't have setMyPhoto method.

    Args:
        bot_username: Bot username without @ (e.g., "my_bot")
        photo_content_b64: Base64-encoded image bytes (Celery requires JSON-serializable args)
        content_type: MIME type of the image

    Returns:
        {"success": True/False, "error": str}
    """
    import base64

    logger.info(f"[USERBOT_TASK] set_bot_photo started for @{bot_username}")

    # Decode base64 back to bytes
    try:
        photo_content = base64.b64decode(photo_content_b64)
        logger.info(f"[USERBOT_TASK] Decoded photo: {len(photo_content)} bytes")
    except Exception as e:
        logger.error(f"[USERBOT_TASK] Failed to decode base64: {e}")
        return {"success": False, "error": f"Failed to decode photo data: {e}"}

    from messenger_bots.services.bot_factory import BotFactoryService

    # Use any available authenticated userbot
    result = _run_async(BotFactoryService._set_bot_photo_async(None, bot_username, photo_content, content_type))

    logger.info(f"[USERBOT_TASK] set_bot_photo result: {result}")
    return result


CHAT_HISTORY_LIMIT = 5

# Telegram message delay (seconds) - used for countdown scheduling
TG_MESSAGE_DELAY = 0.5


@shared_task(bind=True, max_retries=2, default_retry_delay=1)
def send_telegram_message_part_task(
    self,
    telegram_bot_id: int,
    chat_id: int,
    text: str,
    part_index: int,
    reply_markup: dict = None,
):
    """Send a single Telegram message part (for multi-part responses).

    Uses countdown scheduling to avoid blocking workers with time.sleep().
    Each part is sent as a separate task with incremental delay.

    Args:
        telegram_bot_id: TelegramBot ID
        chat_id: BotChat ID
        text: Message text to send
        part_index: Index of this part (0, 1, 2, ...)
        reply_markup: Optional inline keyboard
    """
    logger.debug(f"[TG_PART_TASK] Sending part {part_index} for chat {chat_id}")

    try:
        telegram_bot = TelegramBot.objects.select_related("organization").get(
            id=telegram_bot_id
        )
        chat = BotChat.objects.get(id=chat_id)
    except (TelegramBot.DoesNotExist, BotChat.DoesNotExist) as e:
        logger.error(f"[TG_PART_TASK] Bot or chat not found: {e}")
        return {"success": False, "error": str(e)}

    from messenger_bots.services.telegram import TelegramBotService

    service = TelegramBotService(telegram_bot)
    result = service.send_message(chat.platform_chat_id, text, reply_markup=reply_markup)

    if result:
        msg = BotMessage.objects.create(
            chat=chat,
            sender=BotMessage.ASSISTANT,
            text=text,
            platform_message_id=str(result.get("message_id", "")),
        )
        _send_ws_notification(msg, chat)
        logger.debug(f"[TG_PART_TASK] Part {part_index} sent: {result.get('message_id')}")
        return {"success": True, "message_id": result.get("message_id")}
    else:
        logger.error(f"[TG_PART_TASK] Part {part_index} failed")
        raise self.retry(exc=Exception("Message send failed"))


@shared_task(bind=True, max_retries=3, default_retry_delay=5, time_limit=120, soft_time_limit=100)
def send_telegram_products_task(
    self,
    telegram_bot_id: int,
    chat_id: int,
    products: list,
    footer: str,
    page: int = 0,
    language: str = "ru",
):
    """Send products with pagination asynchronously using countdown scheduling.

    Uses countdown to schedule messages with delays, avoiding time.sleep() blocking.
    This is the orchestrator task that schedules individual message tasks.
    """
    from messenger_bots.services.telegram import (
        TelegramBotService,
        PRODUCTS_PER_PAGE,
    )

    logger.info(f"[TG_PRODUCTS_TASK] Starting: bot_id={telegram_bot_id}, chat_id={chat_id}, page={page}")

    try:
        telegram_bot = TelegramBot.objects.select_related("organization").get(id=telegram_bot_id)
        chat = BotChat.objects.get(id=chat_id)
    except (TelegramBot.DoesNotExist, BotChat.DoesNotExist) as e:
        logger.error(f"[TG_PRODUCTS_TASK] ERROR: {e}")
        return {"success": False, "error": str(e)}

    start = page * PRODUCTS_PER_PAGE
    batch = products[start:start + PRODUCTS_PER_PAGE]
    has_more = (start + PRODUCTS_PER_PAGE) < len(products)

    # Calculate total messages to schedule
    total_messages = len(batch)
    if has_more:
        total_messages += 1  # "Show more" button message
    elif footer:
        total_messages += 1  # Footer message

    # Schedule product messages with countdown delays
    message_index = 0
    for product in batch:
        send_telegram_message_part_task.apply_async(
            args=(telegram_bot_id, chat_id, product, message_index),
            countdown=message_index * TG_MESSAGE_DELAY,
        )
        message_index += 1

    # Schedule pagination or footer
    if has_more:
        remaining = len(products) - (start + PRODUCTS_PER_PAGE)
        show_count = min(remaining, PRODUCTS_PER_PAGE)

        button_text = {
            "ru": f"Показать ещё {show_count}",
            "en": f"Show {show_count} more",
        }
        status_text = {
            "ru": f"Показано {start + len(batch)} из {len(products)} товаров",
            "en": f"Shown {start + len(batch)} of {len(products)} products",
        }

        keyboard = {
            "inline_keyboard": [[{
                "text": button_text.get(language, button_text["ru"]),
                "callback_data": f"{TelegramBotService.CALLBACK_MORE_PRODUCTS}{page + 1}",
            }]]
        }

        send_telegram_message_part_task.apply_async(
            args=(
                telegram_bot_id,
                chat_id,
                status_text.get(language, status_text["ru"]),
                message_index,
            ),
            kwargs={"reply_markup": keyboard},
            countdown=message_index * TG_MESSAGE_DELAY,
        )
    elif footer:
        # Build main menu keyboard for footer
        service = TelegramBotService(telegram_bot)
        keyboard = service.build_main_menu_keyboard(language)

        send_telegram_message_part_task.apply_async(
            args=(telegram_bot_id, chat_id, footer, message_index),
            kwargs={"reply_markup": keyboard},
            countdown=message_index * TG_MESSAGE_DELAY,
        )

    logger.info(f"[TG_PRODUCTS_TASK] Scheduled {total_messages} messages for chat {chat_id}")
    return {"success": True, "messages_scheduled": total_messages}


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

        # Add bot link to organization contacts (regardless of webhook setup)
        from messenger_bots.utils import add_bot_link_to_contacts
        add_bot_link_to_contacts(request.organization, request.bot_username)

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
        # Use stored base_url or fallback to production
        base_url = request.base_url or "https://apofiz.com"
        logger.info(f"Using base_url: {base_url}")
        create_telegram_bot_task.delay(request.id, base_url)

    return {"processed": len(pending_requests)}


@shared_task(bind=True, max_retries=2, default_retry_delay=1)
def send_whatsapp_message_part_task(
    self,
    whatsapp_bot_id: int,
    chat_id: int,
    text: str,
    part_index: int,
):
    """Send a single WhatsApp message part (for multi-part responses).

    Uses countdown scheduling to avoid blocking workers with time.sleep().
    Each part is sent as a separate task with incremental delay.

    Args:
        whatsapp_bot_id: WhatsAppBot ID
        chat_id: BotChat ID
        text: Message text to send
        part_index: Index of this part (0, 1, 2, ...)
    """
    logger.debug(f"[WA_PART_TASK] Sending part {part_index} for chat {chat_id}")

    try:
        whatsapp_bot = WhatsAppBot.objects.select_related("organization").get(
            id=whatsapp_bot_id
        )
        chat = BotChat.objects.get(id=chat_id)
    except (WhatsAppBot.DoesNotExist, BotChat.DoesNotExist) as e:
        logger.error(f"[WA_PART_TASK] Bot or chat not found: {e}")
        return {"success": False, "error": str(e)}

    from messenger_bots.services.whatsapp import WhatsAppServiceFactory
    from messenger_bots.services.whatsapp.base import WhatsAppMessage

    service = WhatsAppServiceFactory.get_service(whatsapp_bot)

    message = WhatsAppMessage(
        to=chat.platform_chat_id,
        text=text,
    )
    result = service.send_message(message)

    if result.success:
        wa_response_msg = BotMessage.objects.create(
            chat=chat,
            sender=BotMessage.ASSISTANT,
            text=text,
            platform_message_id=result.message_id or "",
        )
        _send_ws_notification(wa_response_msg, chat)
        logger.debug(f"[WA_PART_TASK] Part {part_index} sent: {result.message_id}")
        return {"success": True, "message_id": result.message_id}
    else:
        logger.error(f"[WA_PART_TASK] Part {part_index} failed: {result.error}")
        raise self.retry(exc=Exception(result.error))


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_whatsapp_message_task(
    self,
    whatsapp_bot_id: int,
    chat_id: int,
    message_text: str,
    is_first_message: bool = False,
):
    logger.info("[WA_TASK] ====== PROCESS_WHATSAPP_MESSAGE START ======")
    logger.info(f"[WA_TASK] whatsapp_bot_id={whatsapp_bot_id}, chat_id={chat_id}")
    logger.info(f"[WA_TASK] message='{message_text[:100]}...', is_first_message={is_first_message}")

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

    # Initialize WhatsApp service early for activity indicators
    from messenger_bots.services.whatsapp import WhatsAppServiceFactory
    service = WhatsAppServiceFactory.get_service(whatsapp_bot)

    # Mark incoming message as read (show blue checkmarks)
    service.mark_as_read(chat.platform_chat_id)
    logger.debug(f"[WA_TASK] Marked messages as read for {chat.platform_chat_id}")

    # Send welcome message for first contact and return (like Telegram /start)
    user_language = "ru"
    if is_first_message:
        logger.info("[WA_TASK] First message detected, sending welcome...")
        welcome_text = BotAssistantService._get_message("welcome", user_language)
        _send_whatsapp_welcome(service, chat, welcome_text)
        logger.info("[WA_TASK] ====== PROCESS_WHATSAPP_MESSAGE SUCCESS (welcome) ======")
        return {"success": True, "welcome_sent": True}

    # Check if AI is enabled for this bot
    if not whatsapp_bot.is_ai_enabled:
        logger.info(f"[WA_TASK] AI disabled for org {whatsapp_bot.organization_id}, skipping response")
        return {"success": True, "ai_disabled": True}

    # Check if organization subscription is active
    from messenger_bots.services.subscription_check import check_subscription_active
    if not check_subscription_active(whatsapp_bot.organization):
        logger.info(f"[WA_TASK] Subscription expired for org {whatsapp_bot.organization_id}, skipping AI response")
        return {"success": True, "subscription_expired": True}

    chat_history = _get_whatsapp_chat_history(chat)
    logger.debug(f"[WA_TASK] Chat history: {len(chat_history)} messages")

    # Show typing indicator while AI processes
    service.send_typing(chat.platform_chat_id, duration=15000)
    logger.debug(f"[WA_TASK] Typing indicator started")

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
        from messenger_bots.services.whatsapp.base import WhatsAppMessage
        from messenger_bots.services.message_parser import (
            parse_products_from_response,
            split_by_separator,
            clean_response as clean_ai_response,
            AI_SEPARATOR,
        )

        # Use shared parser (same as Telegram) for product detection
        products, footer = parse_products_from_response(response_text)
        logger.info(f"[WA_TASK] Parsed {len(products)} products, footer: {bool(footer)}")

        message_parts = []

        if products:
            # Has products - send each product as separate message
            message_parts = products
            # TODO: Enable footer when WAHA Plus is available (for link previews)
            # if footer:
            #     message_parts.append(footer)
            logger.info(f"[WA_TASK] Using product parsing: {len(message_parts)} messages")
        elif AI_SEPARATOR in response_text:
            # No products but has separator - split by it
            message_parts = split_by_separator(response_text)
            logger.info(f"[WA_TASK] Split by separator: {len(message_parts)} messages")
        else:
            # Single message, just clean any stray separators
            message_parts = [clean_ai_response(response_text)]

        # Single message - send directly
        if len(message_parts) == 1:
            message = WhatsAppMessage(
                to=chat.platform_chat_id,
                text=message_parts[0],
            )
            result = service.send_message(message)

            if result.success:
                wa_response_msg = BotMessage.objects.create(
                    chat=chat,
                    sender=BotMessage.ASSISTANT,
                    text=message_parts[0],
                    platform_message_id=result.message_id or "",
                )
                _send_ws_notification(wa_response_msg, chat)
                logger.info("[WA_TASK] ====== PROCESS_WHATSAPP_MESSAGE SUCCESS ======")
                return {"success": True, "message_ids": [result.message_id], "messages_sent": 1}
            else:
                whatsapp_bot.last_error = result.error
                whatsapp_bot.save(update_fields=["last_error"])
                return {"success": False, "error": result.error}

        # Multiple messages - use countdown scheduling to avoid blocking
        # Schedule first message immediately, rest with countdown delays
        for i, part_text in enumerate(message_parts):
            send_whatsapp_message_part_task.apply_async(
                args=(whatsapp_bot_id, chat_id, part_text, i),
                countdown=i * 0.3,  # 0, 0.3, 0.6, 0.9... seconds
            )

        logger.info("[WA_TASK] ====== PROCESS_WHATSAPP_MESSAGE SUCCESS ======")
        logger.info(f"[WA_TASK] Scheduled {len(message_parts)} messages for {chat.platform_chat_id}")
        return {
            "success": True,
            "messages_scheduled": len(message_parts),
        }

    except Exception as e:
        logger.error(f"[WA_TASK] ERROR: WhatsApp send error: {e}", exc_info=True)
        raise self.retry(exc=e)


def _get_whatsapp_chat_history(chat: BotChat) -> list:
    """Get chat history for WhatsApp context (same limit as Telegram)."""
    # Get last N*2 messages (same as Telegram for consistency)
    messages = chat.messages.order_by("-created_at")[:CHAT_HISTORY_LIMIT * 2]

    history = []
    for msg in reversed(messages):
        history.append(
            {
                "role": "user" if msg.sender == BotMessage.USER else "assistant",
                "content": msg.text,
            }
        )

    return history[-CHAT_HISTORY_LIMIT * 2:]  # Last 5 pairs (10 messages)


def _send_whatsapp_welcome(service, chat: BotChat, welcome_text: str) -> None:
    """Send welcome message for first-time WhatsApp contact.

    Args:
        service: WhatsApp service instance (WAHA/Twilio/etc.)
        chat: BotChat instance
        welcome_text: Welcome message text
    """
    from messenger_bots.services.whatsapp.base import WhatsAppMessage

    try:
        message = WhatsAppMessage(
            to=chat.platform_chat_id,
            text=welcome_text,
        )
        result = service.send_message(message)

        if result.success:
            # Save welcome message to chat history
            welcome_msg = BotMessage.objects.create(
                chat=chat,
                sender=BotMessage.ASSISTANT,
                text=welcome_text,
                platform_message_id=result.message_id,
            )
            _send_ws_notification(welcome_msg, chat)
            logger.info(f"[WA_TASK] Welcome message sent: {result.message_id}")
        else:
            logger.warning(f"[WA_TASK] Failed to send welcome: {result.error}")

    except Exception as e:
        logger.warning(f"[WA_TASK] Welcome message error: {e}")


@shared_task
def ensure_waha_session_running():
    """
    Monitor WAHA session and auto-restart if stopped/failed.

    Runs every 2 minutes to quickly detect and recover from session drops.
    This is critical for OTP bot availability.
    """
    from messenger_bots.models import WhatsAppProvider, WhatsAppSessionStatus
    from messenger_bots.services.whatsapp import WhatsAppServiceFactory

    waha_bots = WhatsAppBot.objects.filter(
        provider=WhatsAppProvider.WAHA,
        is_active=True,
    ).select_related("organization")

    results = []
    for bot in waha_bots:
        try:
            service = WhatsAppServiceFactory.get_service(bot)
            connection_status = service.check_connection()
            waha_status = connection_status.get("status", "UNKNOWN")

            # Session needs restart if STOPPED or FAILED
            if waha_status in ["STOPPED", "FAILED"]:
                logger.warning(
                    f"[WAHA_MONITOR] Session down for org {bot.organization.id}: "
                    f"status={waha_status}, attempting auto-restart..."
                )

                # Attempt to start session
                success = service.start_session()

                if success:
                    logger.info(
                        f"[WAHA_MONITOR] Session auto-restarted for org {bot.organization.id}"
                    )
                    bot.session_status = WhatsAppSessionStatus.PENDING
                    bot.last_error = None
                    bot.save(update_fields=["session_status", "last_error"])
                    results.append({
                        "org_id": bot.organization.id,
                        "action": "restarted",
                        "previous_status": waha_status,
                    })
                else:
                    logger.error(
                        f"[WAHA_MONITOR] Failed to restart session for org {bot.organization.id}"
                    )
                    bot.session_status = WhatsAppSessionStatus.FAILED
                    bot.last_error = f"Auto-restart failed from status: {waha_status}"
                    bot.save(update_fields=["session_status", "last_error"])
                    results.append({
                        "org_id": bot.organization.id,
                        "action": "restart_failed",
                        "previous_status": waha_status,
                    })

            elif waha_status == "WORKING":
                # Session is healthy
                results.append({
                    "org_id": bot.organization.id,
                    "action": "healthy",
                    "status": waha_status,
                })

            elif waha_status == "STARTING":
                # Session is starting, wait for it
                logger.info(
                    f"[WAHA_MONITOR] Session starting for org {bot.organization.id}"
                )
                results.append({
                    "org_id": bot.organization.id,
                    "action": "starting",
                    "status": waha_status,
                })

            else:
                # Unknown or other status (SCAN_QR_CODE, etc.)
                logger.info(
                    f"[WAHA_MONITOR] Session status for org {bot.organization.id}: {waha_status}"
                )
                results.append({
                    "org_id": bot.organization.id,
                    "action": "monitoring",
                    "status": waha_status,
                })

        except Exception as e:
            logger.error(
                f"[WAHA_MONITOR] Error checking session for org {bot.organization.id}: {e}"
            )
            results.append({
                "org_id": bot.organization.id,
                "action": "error",
                "error": str(e),
            })

    logger.info(f"[WAHA_MONITOR] Check completed: {len(results)} bots monitored")
    return {"monitored": len(results), "results": results}


@shared_task
def check_waha_session_health():
    from messenger_bots.models import WhatsAppProvider, WhatsAppSessionStatus
    from messenger_bots.services.whatsapp import WhatsAppServiceFactory

    waha_bots = WhatsAppBot.objects.filter(
        provider=WhatsAppProvider.WAHA,
        is_active=True,
    ).select_related("organization")

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
    ).select_related("organization")

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


# ============== AI Assistant Cache Tasks ==============

CACHE_TIMEOUT = 25 * 60  # 25 minutes (task runs every 20 min, so cache outlives task interval)


@shared_task
def cache_assistant_training_data():
    """
    Pre-cache training data (Q&A, catalog, PDF content) for all active assistants.
    Runs every 20 minutes to keep cache warm.
    Uses parallel file downloads for performance.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from django.core.cache import cache
    from organizations.models import Assistant
    from shop.services.comment_services import CommentService
    from messenger_bots.services.ai_utils import (
        format_catalog_json,
        read_file_from_url,
        get_http_session_with_retry,
    )

    # Get all enabled assistants with active bots
    assistants = Assistant.objects.filter(
        is_enabled=True,
    ).select_related('organization').prefetch_related(
        'organization__telegram_bot',
        'organization__whatsapp_bot',
    )

    cached_count = 0
    errors = []

    for assistant in assistants:
        org = assistant.organization

        # Check if org has active bots (TG or WA)
        has_tg = hasattr(org, 'telegram_bot') and org.telegram_bot.is_active
        has_wa = hasattr(org, 'whatsapp_bot') and org.whatsapp_bot.is_active

        if not (has_tg or has_wa):
            continue

        try:
            from messenger_bots.signals import get_assistant_cache_key
            cache_key = get_assistant_cache_key(org.id)
            logger.info(f"[CACHE_TASK] Caching training data for org {org.id} ({org.title})")

            # Get base training data
            training_data = CommentService.get_training_data(assistant=assistant)

            # Parallel download of files
            qa_pairs = training_data.get("answers", [])
            file_urls = []
            for qa in qa_pairs:
                for file_url in (qa.get('files') or []):
                    if file_url:
                        file_urls.append(file_url)

            # Download files in parallel
            file_contents = {}
            if file_urls:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_url = {
                        executor.submit(read_file_from_url, url): url
                        for url in file_urls
                    }
                    for future in as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            content = future.result()
                            if content:
                                file_contents[url] = content
                        except Exception as e:
                            logger.warning(f"[CACHE_TASK] Failed to download {url}: {e}")

            # Store file contents in training data
            training_data['_cached_file_contents'] = file_contents

            # Download and cache catalog
            catalog_url = training_data.get("catalog_file")
            if catalog_url:
                try:
                    session = get_http_session_with_retry()
                    response = session.get(catalog_url, timeout=(5, 15))
                    response.raise_for_status()
                    catalog_content = format_catalog_json(response.content)
                    training_data['_cached_catalog'] = catalog_content
                    logger.info(f"[CACHE_TASK] Cached catalog: {len(catalog_content)} chars")
                except Exception as e:
                    logger.warning(f"[CACHE_TASK] Failed to download catalog: {e}")

            # Store in cache
            cache.set(cache_key, training_data, timeout=CACHE_TIMEOUT)
            cached_count += 1
            logger.info(f"[CACHE_TASK] Cached org {org.id}: {len(qa_pairs)} Q&A, {len(file_contents)} files")

        except Exception as e:
            logger.error(f"[CACHE_TASK] Error caching org {org.id}: {e}")
            errors.append({"org_id": org.id, "error": str(e)})

    logger.info(f"[CACHE_TASK] Completed: {cached_count} assistants cached, {len(errors)} errors")
    return {"cached": cached_count, "errors": errors}
