import time
import logging
import json
import requests
import re
from django.conf import settings
from django.db import transaction
from django.db.models import Max, Q
from django.utils.translation import gettext_lazy as _
import base64
from common.exceptions import ObjectNotFoundException
from common.models import CommentsWallpaper, File
from common.serializers import ImageSerializer
from instagram_parsers.services.proxy_services import ProxyService
from notifications.constants import NOTIFICATION_MODE_PERSONAL, NEW_COMMENT_TYPE
from notifications.models import Notification
from organizations.models import Membership, Chat, Assistant, Answer, Organization, Coupon, DiscountCard
from organizations.services.assistant_services import AssistantService
from shop.models import Comment, ShopItem, UserCommentTheme, CommentTheme
from users.models import User
from notifications.tasks import sent_notification
from shop.services.assistant_data_service import AssistantDataService

logger = logging.getLogger(__name__)
VIN_REGEX = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.IGNORECASE)


class CommentService:
    model = Comment

    @classmethod
    def _extract_vin_from_text(cls, text: str):
        match = VIN_REGEX.search(text or "")
        if not match:
            return None
        return match.group(0).upper()

    @classmethod
    def _decode_vin_with_nhtsa(cls, vin: str):
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
        try:
            response = requests.get(url, timeout=(5, 15))
            response.raise_for_status()
            payload = response.json()
            results = payload.get("Results") or []

            values = {}
            for row in results:
                variable = (row.get("Variable") or "").strip()
                value = (row.get("Value") or "").strip()
                if variable and value and value.upper() not in {"NULL", "NOT APPLICABLE"}:
                    values[variable] = value

            return {
                "VIN": vin,
                "Make": values.get("Make", ""),
                "Model": values.get("Model", ""),
                "Model Year": values.get("Model Year", ""),
                "Vehicle Type": values.get("Vehicle Type", ""),
                "Body Class": values.get("Body Class", ""),
                "Manufacturer Name": values.get("Manufacturer Name", ""),
                "Engine Model": values.get("Engine Model", ""),
                "Plant Country": values.get("Plant Country", ""),
                "Error Code": values.get("Error Code", ""),
                "Error Text": values.get("Error Text", ""),
            }
        except Exception as error:
            logger.warning("[TRAINING_DATA][VIN] DecodeVin failed for vin=%s: %s", vin, error)
            return None

    @classmethod
    def _append_vin_context_to_training_data(cls, training_data: dict, user_message: str):
        vin = cls._extract_vin_from_text(user_message)
        if not vin:
            return training_data

        decoded = cls._decode_vin_with_nhtsa(vin)
        if decoded:
            lines = [f"- {key}: {value}" for key, value in decoded.items() if value]
            vin_context = (
                "VIN decode data from NHTSA DecodeVin API. "
                "Use this as trusted source when user asks about VIN:\n"
                + "\n".join(lines)
            )
        else:
            vin_context = (
                "VIN decode note: VIN detected in user message, but NHTSA DecodeVin API "
                "did not return usable data. Ask user to verify VIN and try again."
            )

        assistant_info = training_data.setdefault("assistant_info", {})
        current_prompt = assistant_info.get("ai_prompt") or ""
        assistant_info["ai_prompt"] = (
            f"{current_prompt}\n\n{vin_context}" if current_prompt else vin_context
        )

        answers = training_data.setdefault("answers", [])
        vin_answer = {
            "question": f"VIN {vin}",
            "answer": vin_context,
            "files_to_read": [],
            "files_to_send": [],
            "files": [],
        }
        answers.insert(0, vin_answer)

        training_data["vin_lookup_context"] = vin_context
        training_data["vin_lookup"] = {
            "detected": True,
            "vin": vin,
            "decoded": decoded or {},
        }
        logger.info(
            "[TRAINING_DATA][VIN] VIN context added: vin=%s decoded=%s",
            vin,
            bool(decoded),
        )
        return training_data

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Comment not found'))

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def create_comment(cls, text: str, item: ShopItem, user: User, parent: Comment = None):
        comment = cls.model.objects.create(item=item, user=user, parent=parent, text=text)

        if item.organization.owner != user:
            sent_notification.delay(
                recipient_id=item.organization.owner.id,
                sender_id=user.id,
                mode=NOTIFICATION_MODE_PERSONAL,
                notification_type=NEW_COMMENT_TYPE,
                item_id=item.id,
                organization_id=item.organization.id,
                extra_data=dict(
                    comment_id=comment.id,
                    comment_text=text)
            )
        return comment

    @classmethod
    def create_item_comment(cls, text: str, item: ShopItem, user: User, parent: Comment = None):
        comment = cls.model.objects.create(item=item, user=user, parent=parent, text=text)

        return comment

    @classmethod
    def create_assistant_comment(cls, text: str, item: ShopItem, assistant: Assistant, parent: Comment = None):
        comment = cls.model.objects.create(item=item, assistant=assistant, parent=parent, text=text)

        return comment

    @classmethod
    def create_chat_comment(cls, text: str, chat: Chat, user: User, parent: Comment = None, user_audio_file=None, skip_assistant_reply=False):
        if not text and user_audio_file:
            text = "[Голосовое сообщение]"
        comment = cls.model.objects.create(chat=chat, user=user, parent=parent, text=text)
        # Пробросить skip_assistant_reply в объект комментария через атрибут (если нужно)
        comment.skip_assistant_reply = skip_assistant_reply
        if user_audio_file:
            comment.user_audio.save(user_audio_file.name, user_audio_file, save=True)
        return comment

    @classmethod
    def create_chat_assistant_comment(cls, text: str, chat: Chat, assistant: Assistant, parent: Comment = None, audio_file=None):
        comment = cls.model.objects.create(chat=chat, assistant=assistant, parent=parent, text=text)

        if audio_file:
            comment.audio.save(audio_file.name, audio_file, save=True)
        return comment

    @classmethod
    def create_item_assistant_comment(cls, text: str, item: ShopItem, assistant: Assistant, parent: Comment = None):
        comment = cls.model.objects.create(item=item, assistant=assistant, parent=parent, text=text)

        return comment

    @classmethod
    def create_chat_assistant_default_comment(cls, chat: Chat, assistant: Assistant):
        text = _("Good afternoon! Nice to meet you, how can I help you?")
        comment = cls.model.objects.create(chat=chat, assistant=assistant, text=text)

        return comment

    @classmethod
    def get_training_data(cls, assistant: Assistant, user_message: str = None):
        answers = Answer.objects.filter(assistant=assistant)
        org = Organization.objects.get(assistant=assistant)
        catalog_url = AssistantDataService.get_file_url(assistant.organization)
        
        logger.info(
            f"[TRAINING_DATA] Preparing training data for assistant={assistant.id}, "
            f"org_id={org.id}, catalog_url={catalog_url}"
        )
        organization_info = {
            "name": org.title,
            "description": org.description or "",
            "address": org.address or "",
            "opens_at": str(org.opens_at) if org.opens_at else "",
            "closes_at": str(org.closes_at) if org.closes_at else "",
        }

        phone_numbers = list(org.phone_numbers.values_list("phone_number", flat=True))
        if phone_numbers:
            organization_info["phones"] = ", ".join(phone_numbers)

        social_contacts = list(org.social_contacts.values_list("url", flat=True))

        if social_contacts:
            organization_info["social_links"] = ", ".join(social_contacts)

        marketing_info = []
        discounts = DiscountCard.objects.filter(organization=org, is_published=True)
        coupons = Coupon.objects.filter(organization=org, is_active=True)
        coupons_info = []
        for coupon in coupons:
            coupons_info.append(f"{coupon.percent} - {coupon.description}")

        for card in discounts:
            if card.type == DiscountCard.FIXED:
                marketing_info.append(f"Постоянная скидка: {card.percent}%")

            elif card.type == DiscountCard.CASHBACK:
                marketing_info.append(f"Кэшбек: {card.percent}%")

            elif card.type == DiscountCard.CUMULATIVE:
                limit_str = f"{card.limit} {card.currency.code}" if card.limit and card.currency else "определенной суммы"
                marketing_info.append(f"Накопительная скидка {card.percent}% (при покупках от {limit_str})")

        org_url = f"{settings.SITE_URL}/organizations/{org.id}"
        training_data = {
            "assistant_info": {
                "organization": org.title,
                "name": assistant.name,
                "gender": assistant.gender,
                "position": assistant.position,
                "is_enabled": assistant.is_enabled,
                "ai_prompt": assistant.ai_prompt,
                "first_message": assistant.first_message,
                "ai_voice": assistant.ai_voice,
            },
            "answers": [],
            "organization_page_url": org_url,
            "catalog_file": catalog_url,
            "organization_info":organization_info,
            "marketing_info": marketing_info,
            "coupons_info": coupons_info,
        }

        for answer in answers:
            files_to_read = []
            files_to_send = []
            
            for file_obj in answer.files.all():
                if file_obj.is_readable_by_ai:
                    files_to_read.append(file_obj.file.url)
                else:
                    files_to_send.append(file_obj.file.url)

            question_text = (
                (answer.question.text if answer.question else None)
                or "Вопрос не указан"
            )
            question_preview = str(question_text)[:80]

            logger.debug(
                f"[TRAINING_DATA] answer_id={answer.id}, question='{question_preview}', "
                f"files_to_read={len(files_to_read)}, files_to_send={len(files_to_send)}"
            )

            logger.debug(
                f"[TRAINING_DATA] answer_id={answer.id}, question='{question_text[:80]}', "
                f"files_to_read={len(files_to_read)}, files_to_send={len(files_to_send)}"
            )

            training_data["answers"].append({
                "question": question_text,
                "answer": answer.text,
                "files_to_read": files_to_read,
                "files_to_send": files_to_send,
                # Backward-compatible key used by prompt builder/cache task
                "files": files_to_read,
            })

        if user_message:
            training_data = cls._append_vin_context_to_training_data(
                training_data=training_data,
                user_message=user_message,
            )

        logger.info(
            f"[TRAINING_DATA] Completed training data for assistant={assistant.id}: "
            f"catalog_url={catalog_url}, "
            f"answers_count={len(training_data['answers'])}, "
            f"marketing_count={len(marketing_info)}, coupons_count={len(coupons_info)}"
        )
        try:
            training_data_json = json.dumps(
                training_data,
                ensure_ascii=False,
                default=str,
            )
            logger.info("[TRAINING_DATA_FULL_JSON_LENGTH] %s", len(training_data_json))
            logger.info(
                "[TRAINING_DATA_FULL_START]%s[TRAINING_DATA_FULL_END]",
                training_data_json,
            )
        except Exception as error:
            logger.exception("[TRAINING_DATA_FULL_LOG_ERROR] %s", error)
        return training_data

    @classmethod
    def create_chat_comment_with_assistant_response(cls, text: str, chat: Chat, user: User, request,
                                                parent: Comment = None, user_audio_file=None):

        if not text and user_audio_file:
            text = "[Голосовое сообщение]"

        comment = cls.model.objects.create(chat=chat, user=user, parent=parent, text=text)
        user_audio_base64 = ""
        if user_audio_file:

            comment.user_audio.save(user_audio_file.name, user_audio_file, save=True)

            try:
                user_audio_file.seek(0) 
                user_audio_base64 = base64.b64encode(user_audio_file.read()).decode('utf-8')
            except Exception as e:
                logger.error(f"Error encoding user audio for AI server: {e}")

        host = request.META.get('HTTP_HOST', 'default_host')
        
        request_headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "User-Agent": "Apofiz-Main-Server-1.0",
        }

        ask_bot_url = 'http://161.35.153.151:8080/bot/'

        data = {
            "assistant_id": chat.assistant.id,
            "parent_id": comment.id,
            "chat_id": chat.id,
            "message": comment.text,
            "user_audio": user_audio_base64, 
            "host": host,
            "training_data": cls.get_training_data(
                assistant=chat.assistant,
                user_message=comment.text,
            )
        }

        sess = requests.Session()
        try:
            response = sess.post(ask_bot_url, json=data, headers=request_headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to communicate with AI assistant: {e}")

        return comment

    @classmethod
    def create_chat_comment_with_assistant_default_response(cls, text: str, chat: Chat, user: User,
                                                            parent: Comment = None):
        user_comment = cls.create_chat_comment(chat=chat, user=user, text=text, parent=parent)

        assistant_text = _("Sorry, I'm on vacation!")

        cls.model.objects.create(chat=chat, assistant=chat.assistant, parent=user_comment, text=assistant_text)

        return user_comment

    @classmethod
    def create_ws_chat_comment_with_assistant_default_response(cls, chat: Chat, parent: Comment = None):
        assistant_text = _("Sorry, I'm on vacation!")

        ai_assistant = cls.model.objects.create(chat=chat, assistant=chat.assistant, parent=parent, text=assistant_text)

        return ai_assistant

    @classmethod
    def delete_comment(cls, comment: Comment):
        # transaction.on_commit(
        #     lambda: Notification.objects.filter(
        #         Q(extra_data__comment_id=comment.id) & Q(type=NEW_COMMENT_TYPE)
        #     ).delete()
        # )
        comment.delete()

    @classmethod
    def get_income_commented_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, comments__item__organization__owner=user,
                                       organization__is_deleted=False).distinct().annotate(
            comment_date=Max('comments__created_at')).order_by('-comment_date')

    @classmethod
    def get_outcome_commented_items(cls, user: User):
        comments = Comment.objects.filter(user=user)
        return ShopItem.objects.filter(is_published=True, comments__in=comments,
                                       organization__is_deleted=False).distinct().annotate(
            comment_date=Max('comments__created_at')).order_by('-comment_date')

    @classmethod
    def get_my_role(cls, user: User, item: ShopItem):
        try:
            membership = Membership.objects.get(organization=item.organization, user=user)
            return membership.role.title
        except Membership.DoesNotExist:
            if item.organization.owner == user:
                return 'is_owner'
            return None

    @classmethod
    def get_my_role_for_chat(cls, user: User, chat: Chat):
        try:
            membership = Membership.objects.get(organization=chat.assistant.organization, user=user)
            return membership.role.title
        except Membership.DoesNotExist:
            if chat.assistant.organization.owner == user:
                return 'is_owner'
            return None

    @classmethod
    def get_wallpapers(cls):
        wallpaper = CommentsWallpaper.objects.filter(is_active=True).first()
        if wallpaper:
            return {'web': 'https://apofiz-media.s3.eu-central-1.amazonaws.com/' + str(wallpaper.web_image),
                    'mobile': 'https://apofiz-media.s3.eu-central-1.amazonaws.com/' + str(wallpaper.mobile)}
        else:
            return None

    @classmethod
    def get_user_theme_or_default(cls, user: User):
        user_theme = UserCommentTheme.objects.filter(user=user).first()
        default_theme = CommentTheme.objects.filter(is_active=True).first()

        if user_theme:
            return {
                "theme_type": user_theme.theme_type,
                "theme_id": user_theme.theme_id,
                "image": ImageSerializer(user_theme.image).data if user_theme.image else None,
                "svg_background": default_theme.svg_background.url if default_theme.svg_background else "",
                "svg_pattern": default_theme.svg_pattern.url if default_theme.svg_pattern else ""
            }
        else:

            if default_theme:
                user_theme, created = UserCommentTheme.objects.get_or_create(user=user,
                                                                             defaults={'theme_type': 'default'})
                return {
                    "theme_type": default_theme.theme_type,
                    "theme_id": None,
                    "image": ImageSerializer(user_theme.image).data if user_theme.image else None,
                    "svg_background": default_theme.svg_background.url if default_theme.svg_background else "",
                    "svg_pattern": default_theme.svg_pattern.url if default_theme.svg_pattern else ""
                }
            else:
                return None

    @classmethod
    def update_user_theme(cls, user, theme_type, theme_id=None, image_id=None):
        user_theme, created = UserCommentTheme.objects.get_or_create(user=user)
        user_theme.theme_type = theme_type

        default_theme = CommentTheme.objects.filter(is_active=True).first()

        if theme_type == 'custom' and image_id:
            user_theme.image = File.objects.get(id=image_id)
            user_theme.theme_id = None

        elif theme_type == 'predefined' and theme_id:
            user_theme.theme_id = theme_id

        elif theme_type == 'default':
            if default_theme:
                user_theme.theme_id = None
            else:
                return None

        user_theme.save()

        return {
            "theme_type": user_theme.theme_type,
            "theme_id": user_theme.theme_id,
            "image": ImageSerializer(user_theme.image).data if user_theme.image else None,
            "svg_background": default_theme.svg_background.url if default_theme.svg_background else "",
            "svg_pattern": default_theme.svg_pattern.url if default_theme.svg_pattern else ""
        }

    @classmethod
    def do_read_messages(cls, chat: Chat):
        return cls.filter(is_read=False, chat=chat).update(is_read=True)


