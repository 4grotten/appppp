from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from common.models import File
from common.serializers import ImageSerializer
from organizations.models import Assistant, Organization, Answer, AnswerFile, Question, Plan, ChatMessage, Chat, \
    UserAssistant
from organizations.services.assistant_services import AssistantService
from organizations.services.organization_services import OrganizationService
from users.models import User
from users.serializers import UserShortInfoSerializer


class AnswerFileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = AnswerFile
        fields = ('id', 'file', 'name')
        read_only_fields = ('name',)

    def get_name(self, obj):
        return obj.file.name.split("/")[-1]


class AssistantCreateSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(required=True, queryset=Organization.objects.all())

    class Meta:
        model = Assistant
        fields = ('id', 'organization', 'name', 'gender', 'position', 'image')

    def validate_organization(self, organization):
        if AssistantService.exists_for_organization(organization=organization):
            raise serializers.ValidationError(_('Assistant already exists in this organization.'))
        return organization


class OrganizationAssistantAnswerCreateSerializer(serializers.ModelSerializer):
    files = serializers.PrimaryKeyRelatedField(queryset=AnswerFile.objects.all(), many=True, required=False)

    class Meta:
        model = Answer
        fields = ('id', 'assistant', 'question', 'text', 'files')

    def create(self, validated_data):
        files = validated_data.pop('files', [])
        answer = Answer.objects.create(**validated_data)
        answer.files.set(files)
        return answer


class OrganizationAssistantSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), source='image', write_only=True, required=False
    )
    is_assistant_active = serializers.SerializerMethodField()

    class Meta:
        model = Assistant
        fields = ('id', 'organization', 'name', 'gender', 'position', 'image', 'image_id', 'is_assistant_active')
        read_only_fields = ('organization', )

    def get_is_assistant_active(self, assistant: Assistant):
        user = self.context['request'].user
        user_assistants = UserAssistant.objects.filter(assistant=assistant, user=user, is_active=True)

        if user_assistants.exists():
            longest_active_user_assistant = user_assistants.order_by('-active_until').first()
            user_assistants.exclude(id=longest_active_user_assistant.id).update(is_active=False)

            is_assistant_active = longest_active_user_assistant.active_until and longest_active_user_assistant.active_until > timezone.now()
            return is_assistant_active
        return False


class OrganizationAssistantUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), source='image', write_only=True, required=False
    )

    class Meta:
        model = Assistant
        fields = ('id', 'organization', 'name', 'gender', 'position', 'image_id')
        read_only_fields = ('organization', )


class OrganizationAssistantAnswerRetrieveSerializer(serializers.ModelSerializer):
    files = AnswerFileSerializer(many=True)

    class Meta:
        model = Answer
        fields = ('id', 'assistant', 'question', 'text', 'files')


class OrganizationAssistantAnswerUpdateSerializer(serializers.ModelSerializer):
    files = serializers.PrimaryKeyRelatedField(queryset=AnswerFile.objects.all(), many=True, required=False)

    class Meta:
        model = Answer
        fields = ('id', 'assistant', 'question', 'text', 'files')

    def update(self, instance, validated_data):
        files_data = validated_data.pop('files', [])
        instance.text = validated_data.get('text', instance.text)
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
        fields = ['id', 'text', 'ordering', 'created_at', 'updated_at', 'is_filled', 'answer']

    def get_answer(self, question: Question):
        assistant = self.context.get('assistant')
        answer = Answer.objects.filter(question=question, assistant=assistant).last()
        if answer:
            return OrganizationAssistantAnswerRetrieveSerializer(answer).data
        return None

    def get_is_filled(self, question: Question):
        assistant = self.context.get('assistant')
        return Answer.objects.filter(question=question, assistant=assistant).exists()


class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan
        fields = ('id', 'name', 'description', 'additional_name', 'price', 'currency', 'is_best_choice')


class AssistantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Assistant
        fields = ('id', 'name', 'gender', 'position', 'image')


class PurchaseAssistantSerializer(serializers.Serializer):
    assistant = serializers.PrimaryKeyRelatedField(queryset=Assistant.objects.all())
    plans = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), many=True)
    duration_days = serializers.IntegerField()
    utc_offset_minutes = serializers.IntegerField(min_value=-720, max_value=840)


class ChatSerializerQueryParam(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    assistant = serializers.PrimaryKeyRelatedField(queryset=Assistant.objects.all())


class ChatMessageSerializer(serializers.ModelSerializer):

    def get_organization(self, chat: Chat):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(organization=chat.assistant.organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=chat.assistant.organization, user=chat.user):
                from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
                return OrganizationWithTypeImageSerializer(chat.assistant.organization).data
        return None

    class Meta:
        model = ChatMessage
        fields = ('id', 'chat', 'parent', 'sender', 'text')

class ChatUserInfoSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer()


    class Meta:
        model = User
        fields = ('id', 'full_name', 'avatar', 'username')

class ChatSerializer(serializers.ModelSerializer):
    user = UserShortInfoSerializer()
    organization = serializers.SerializerMethodField()
    assistant = OrganizationAssistantSerializer()
    user_role = serializers.SerializerMethodField()

    def get_organization(self, chat: Chat):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(organization=chat.assistant.organization, user=user):
            if OrganizationService.user_can_edit_organization(organization=chat.assistant.organization, user=chat.user):
                from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
                return OrganizationWithTypeImageSerializer(chat.assistant.organization).data
        return None

    def get_user_role(self, chat: Chat):
        return AssistantService.get_my_role(assistant=chat.assistant, user=chat.user)

    class Meta:
        model = Chat
        fields = ('id', 'user', 'assistant', 'organization', 'user_role', 'assistant_enabled', 'chat_by_org_user')


class ChatByOrgUserSerializer(serializers.Serializer):
    chat = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all())
    chat_by_org_user = serializers.BooleanField()


class MessageCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatMessage
        fields = ('chat', 'text')


class ChatListSerializer(serializers.ModelSerializer):
    user = UserShortInfoSerializer()
    assistant = OrganizationAssistantSerializer()
    last_message = serializers.SerializerMethodField()
    last_message_created_at = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'user', 'assistant', 'assistant_enabled', 'chat_by_org_user', 'last_message',
                  'last_message_created_at', 'unread_messages_count')

    def get_last_message(self, chat: Chat):
        last_message = chat.chat_messages.order_by('-created_at').first()
        return last_message.text if last_message else None

    def get_last_message_created_at(self, chat: Chat):
        last_message = chat.chat_messages.order_by('-created_at').first()
        return last_message.created_at if last_message else None

    def get_unread_messages_count(self, chat: Chat):
        return chat.chat_messages.filter(is_read=False).count()







