from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.models import File
from common.serializers import ImageSerializer
from organizations.models import (
    Answer,
    AnswerFile,
    Assistant,
    BlockedUser,
    Chat,
    ChatMessage,
    ChatSource,
    Organization,
    Plan,
    Question,
    UserAssistant,
)
from organizations.services.assistant_services import AssistantService
from organizations.services.organization_services import OrganizationService
from users.models import User
from users.serializers import UserShortInfoSerializer


class AnswerFileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = AnswerFile
        fields = ("id", "file", "name","is_readable_by_ai")
        read_only_fields = ("name",)

    def get_name(self, obj):
        return obj.file.name.split("/")[-1]


class AssistantCreateSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        required=True, queryset=Organization.objects.all()
    )

    class Meta:
        model = Assistant
        fields = ("id", "organization", "name", "gender", "position", "image")

    def validate_organization(self, organization):
        if AssistantService.exists_for_organization(organization=organization):
            raise serializers.ValidationError(
                _("Assistant already exists in this organization.")
            )
        return organization


class OrganizationAssistantAnswerCreateSerializer(serializers.ModelSerializer):
    files = serializers.PrimaryKeyRelatedField(
        queryset=AnswerFile.objects.all(), many=True, required=False
    )

    class Meta:
        model = Answer
        fields = ("id", "assistant", "question", "text", "files")

    def create(self, validated_data):
        files = validated_data.pop("files", [])
        answer = Answer.objects.create(**validated_data)
        answer.files.set(files)
        return answer


class OrganizationAssistantSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), source="image", write_only=True, required=False
    )
    is_assistant_active = serializers.SerializerMethodField()
    active_until = serializers.SerializerMethodField()
    is_enabled = serializers.BooleanField(read_only=True)
    plans = serializers.SerializerMethodField()

    class Meta:
        model = Assistant
        fields = (
            "id",
            "organization",
            "name",
            "gender",
            "position",
            "image",
            "image_id",
            "is_assistant_active",
            "active_until",
            "is_enabled",
            "plans",
        )
        read_only_fields = ("organization",)

    def get_active_until(self, assistant):
        user_assistants = UserAssistant.objects.filter(
            assistant=assistant, is_active=True
        )
        if user_assistants.exists():
            longest_active_user_assistant = user_assistants.order_by(
                "-active_until"
            ).first()
            return (
                longest_active_user_assistant.active_until.isoformat()
                if longest_active_user_assistant.active_until
                else None
            )
        return None

    def get_is_assistant_active(self, assistant):
        user_assistants = UserAssistant.objects.filter(
            assistant=assistant, is_active=True
        )
        if user_assistants.exists():
            longest_active_user_assistant = user_assistants.order_by(
                "-active_until"
            ).first()
            user_assistants.exclude(id=longest_active_user_assistant.id).update(
                is_active=False
            )

            is_assistant_active = (
                longest_active_user_assistant.active_until
                and longest_active_user_assistant.active_until > timezone.now()
            )
            return is_assistant_active
        return False

    def get_plans(self, assistant):
        user_assistants = UserAssistant.objects.filter(
            assistant=assistant, is_active=True
        )
        if user_assistants.exists():
            longest_active_user_assistant = user_assistants.order_by(
                "-active_until"
            ).first()
            plans = longest_active_user_assistant.plans
            return list(plans.values_list("id", flat=True)) if plans else []
        return []


class OrganizationAssistantUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), source="image", write_only=True, required=False
    )

    class Meta:
        model = Assistant
        fields = ("id", "organization", "name", "gender", "position", "image_id")
        read_only_fields = ("organization",)


class OrganizationAssistantAnswerRetrieveSerializer(serializers.ModelSerializer):
    files = AnswerFileSerializer(many=True)

    class Meta:
        model = Answer
        fields = ("id", "assistant", "question", "text", "files")


class OrganizationAssistantAnswerUpdateSerializer(serializers.ModelSerializer):
    files = serializers.PrimaryKeyRelatedField(
        queryset=AnswerFile.objects.all(), many=True, required=False
    )

    class Meta:
        model = Answer
        fields = ("id", "assistant", "question", "text", "files")

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        instance.text = validated_data.get("text", instance.text)
        if files_data is not None:
            instance.files.clear()
            for file_data in files_data:
                answer_file = AnswerFile.objects.create(**file_data)
                instance.files.add(answer_file)
        instance.save()
        return instance


class QuestionListQueryParamSerializer(serializers.Serializer):
    assistant_id = serializers.IntegerField(required=True)


class QuestionListSerializer(serializers.ModelSerializer):
    answer = serializers.SerializerMethodField()
    is_filled = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "ordering",
            "created_at",
            "updated_at",
            "is_filled",
            "answer",
        ]

    def get_answer(self, question: Question):
        assistant = self.context.get("assistant")
        answer = Answer.objects.filter(question=question, assistant=assistant).last()
        if answer:
            return OrganizationAssistantAnswerRetrieveSerializer(answer).data
        return None

    def get_is_filled(self, question: Question):
        assistant = self.context.get("assistant")
        return Answer.objects.filter(question=question, assistant=assistant).exists()


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "description",
            "additional_name",
            "price",
            "currency",
            "is_best_choice",
        )


class AssistantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assistant
        fields = ("id", "name", "gender", "position", "image")


class PurchaseAssistantSerializer(serializers.Serializer):
    assistant = serializers.PrimaryKeyRelatedField(queryset=Assistant.objects.all())
    plans = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), many=True)
    duration_days = serializers.IntegerField()
    utc_offset_minutes = serializers.IntegerField(min_value=-720, max_value=840)


class ChatSerializerQueryParam(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    assistant = serializers.PrimaryKeyRelatedField(queryset=Assistant.objects.all())
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        user = attrs.get('user')
        phone = attrs.get('phone')
        if not user and not phone:
            raise serializers.ValidationError("Either 'user' or 'phone' is required")
        return attrs


class ChatMessageSerializer(serializers.ModelSerializer):
    def get_organization(self, chat: Chat):
        user = self.context["request"].user
        if not OrganizationService.user_can_edit_organization(
            organization=chat.assistant.organization, user=user
        ):
            if OrganizationService.user_can_edit_organization(
                organization=chat.assistant.organization, user=chat.user
            ):
                from organizations.serializers.organization_serializers import (
                    OrganizationWithTypeImageSerializer,
                )

                return OrganizationWithTypeImageSerializer(
                    chat.assistant.organization
                ).data
        return None

    class Meta:
        model = ChatMessage
        fields = ("id", "chat", "parent", "sender", "text")


class ChatUserInfoSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer()

    class Meta:
        model = User
        fields = ("id", "full_name", "avatar", "username")


class ChatSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    assistant = OrganizationAssistantSerializer()
    user_role = serializers.SerializerMethodField()
    can_comment = serializers.SerializerMethodField(default=True, read_only=True)
    is_my_chat = serializers.SerializerMethodField()
    source = serializers.CharField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)

    def get_user(self, chat: Chat):
        if chat.source == ChatSource.WEB and chat.user:
            return UserShortInfoSerializer(chat.user).data
        elif chat.bot_chat:
            return TelegramUserInfoSerializer(chat).data
        return None

    def get_can_comment(self, chat: Chat) -> bool:
        if self.context["request"].user:
            user = self.context["request"].user
            blocked_users = (
                BlockedUser.objects.filter(
                    organization_id=chat.assistant.organization.id, user=user.id
                )
                .values_list("user_id", flat=True)
                .distinct()
            )
            return not BlockedUser.objects.filter(user_id__in=blocked_users).exists()

    def get_organization(self, chat: Chat):
        user = self.context["request"].user
        if not OrganizationService.user_can_edit_organization(
            organization=chat.assistant.organization, user=user
        ):
            if chat.user and OrganizationService.user_can_edit_organization(
                organization=chat.assistant.organization, user=chat.user
            ):
                from organizations.serializers.organization_serializers import (
                    OrganizationWithTypeImageSerializer,
                )

                return OrganizationWithTypeImageSerializer(
                    chat.assistant.organization
                ).data
        return None

    def get_user_role(self, chat: Chat):
        if chat.user:
            return AssistantService.get_my_role(assistant=chat.assistant, user=chat.user)
        return None

    def get_is_my_chat(self, chat: Chat):
        user = self.context["request"].user
        return chat.user == user if chat.user else False

    class Meta:
        model = Chat
        fields = (
            "id",
            "user",
            "assistant",
            "organization",
            "user_role",
            "chat_by_org_user",
            "can_comment",
            "is_my_chat",
            "source",
            "is_read",
            "unread_count",
        )


class ChatByOrgUserSerializer(serializers.Serializer):
    chat = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all())
    chat_by_org_user = serializers.BooleanField()


class ToggleAssistantSerializer(serializers.Serializer):
    assistant = serializers.PrimaryKeyRelatedField(queryset=Assistant.objects.all())
    is_enabled = serializers.BooleanField()


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("chat", "text")


class BotUserInfoSerializer(serializers.Serializer):
    """Serializer for Telegram/WhatsApp user info from BotChat."""
    id = serializers.SerializerMethodField()
    full_name = serializers.CharField(source="bot_chat.user_name")
    avatar = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    def get_id(self, chat: Chat):
        """Return bot_chat.id for Telegram, None for WhatsApp (use phone instead)."""
        if chat.bot_chat and chat.source == ChatSource.WHATSAPP:
            return None
        return chat.bot_chat.id if chat.bot_chat else None

    def get_avatar(self, chat: Chat):
        if chat.bot_chat and chat.bot_chat.user_photo:
            return {"image": chat.bot_chat.user_photo}
        return None

    def get_username(self, chat: Chat):
        return None

    def get_phone(self, chat: Chat):
        """Return phone number for WhatsApp chats."""
        if chat.bot_chat and chat.source == ChatSource.WHATSAPP:
            return chat.bot_chat.user_phone
        return None


# Alias for backwards compatibility
TelegramUserInfoSerializer = BotUserInfoSerializer


class ChatListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    assistant = OrganizationAssistantSerializer()
    last_message = serializers.SerializerMethodField()
    last_message_created_at = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()
    source = serializers.CharField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Chat
        fields = (
            "id",
            "user",
            "assistant",
            "chat_by_org_user",
            "last_message",
            "last_message_created_at",
            "unread_messages_count",
            "source",
            "is_read",
        )

    def get_user(self, chat: Chat):
        if chat.source == ChatSource.WEB and chat.user:
            return UserShortInfoSerializer(chat.user).data
        elif chat.bot_chat:
            return TelegramUserInfoSerializer(chat).data
        return None

    def get_last_message(self, chat: Chat):
        # Try annotated values first (N+1 optimized)
        web_text = getattr(chat, '_web_last_message_text', None)
        if web_text:
            return web_text

        tg_text = getattr(chat, '_tg_last_message_text', None)
        if tg_text:
            return tg_text

        # Fallback to query
        last_message = None
        if chat.source == ChatSource.WEB:
            # Web chats use Comment model (related_name='comments')
            last_message = chat.comments.order_by("-created_at").first()
        if not last_message and chat.bot_chat_id:
            if chat.bot_chat:
                last_message = chat.bot_chat.messages.order_by("-created_at").first()

        return last_message.text if last_message else None

    def get_last_message_created_at(self, chat: Chat):
        # Try annotated values first (N+1 optimized)
        web_time = getattr(chat, '_web_last_message_time', None)
        if web_time:
            return web_time

        tg_time = getattr(chat, '_tg_last_message_time', None)
        if tg_time:
            return tg_time

        # Fallback to query
        last_message = None
        if chat.source == ChatSource.WEB:
            # Web chats use Comment model (related_name='comments')
            last_message = chat.comments.order_by("-created_at").first()
        if not last_message and chat.bot_chat_id:
            if chat.bot_chat:
                last_message = chat.bot_chat.messages.order_by("-created_at").first()

        return last_message.created_at if last_message else None

    def get_unread_messages_count(self, chat: Chat):
        # Use denormalized field if available
        return chat.unread_count


class ChatSettingsSerializer(serializers.ModelSerializer):
    can_comment = serializers.SerializerMethodField(default=True, read_only=True)

    class Meta:
        model = Chat
        fields = ("id", "chat_by_org_user", "can_comment")

    def get_can_comment(self, chat: Chat) -> bool:
        if self.context["request"].user:
            user = self.context["request"].user
            blocked_users = (
                BlockedUser.objects.filter(
                    organization_id=chat.assistant.organization.id, user=user.id
                )
                .values_list("user_id", flat=True)
                .distinct()
            )
            return not BlockedUser.objects.filter(user_id__in=blocked_users).exists()


class CreateDescriptionSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        name = attrs.get("name", "").strip()
        description = attrs.get("description", "").strip()

        if not name and not description:
            raise serializers.ValidationError(
                "At least one field (name or description) must be filled"
            )
        return attrs
