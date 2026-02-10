import logging

import requests
from django.conf import settings
from django.db import models
from django.db.models import BooleanField, Case, F, Max, OuterRef, Subquery, Value, When
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from shop.tasks import update_assistant_json_task
from rest_framework.filters import SearchFilter

logger = logging.getLogger(__name__)

from common.exceptions import NotAcceptableException
from organizations.models import Answer, AnswerFile, Assistant, Chat, ChatSource, Plan, Question
from messenger_bots.models import BotChat, BotPlatform
from organizations.serializers.assistant_serializers import (
    AnswerFileSerializer,
    AssistantCreateSerializer,
    ChatByOrgUserSerializer,
    ChatListSerializer,
    ChatSerializer,
    ChatSerializerQueryParam,
    OrganizationAssistantAnswerCreateSerializer,
    OrganizationAssistantAnswerRetrieveSerializer,
    OrganizationAssistantSerializer,
    PlanSerializer,
    PurchaseAssistantSerializer,
    QuestionListQueryParamSerializer,
    QuestionListSerializer,
    ToggleAssistantSerializer, AssistantSettingsUpdateSerializer,
)
from organizations.services.assistant_services import (
    AnswerService,
    AssistantService,
    ChatService,
)
from organizations.services.organization_services import OrganizationService
from shop.services.comment_services import CommentService


class OrganizationAssistantCreateView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AssistantCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']

        if not OrganizationService.user_can_edit_organization(organization=organization, user=request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})

        instance = serializer.save()
        data = OrganizationAssistantSerializer(instance, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationAssistantAnswerCreateView(APIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = OrganizationAssistantAnswerCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        assistant = serializer.validated_data['assistant']

        if not OrganizationService.user_can_edit_organization(organization=assistant.organization, user=request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})

        serializer.save()

        return Response(data={"message": "Answer successfully created"}, status=status.HTTP_201_CREATED)


class OrganizationAssistantRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Assistant.objects.all()
    serializer_class = OrganizationAssistantSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return AssistantService.get(id=self.kwargs['pk'])


class OrganizationAssistantAnswerRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = OrganizationAssistantAnswerCreateSerializer
    queryset = Answer.objects.all()

    def get_object(self):
        answer = AnswerService.get(id=self.kwargs['id'])
        if not OrganizationService.user_can_edit_organization(organization=answer.assistant.organization,
                                                              user=self.request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})
        return answer

    def get(self, request, *args, **kwargs):
        answer = self.get_object()
        serializer = OrganizationAssistantAnswerRetrieveSerializer(answer)
        return Response(serializer.data)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        answer = self.get_object()
        serializer = self.get_serializer(answer, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnswerFileCreateView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, )
    parser_classes = (MultiPartParser,)
    serializer_class = AnswerFileSerializer
    queryset = AnswerFile.objects.all()

    def perform_create(self, serializer):
        question_id = self.request.data.get('question_id')
        is_readable = True
        if question_id and int(question_id) == 9:
            is_readable = False

        serializer.save(is_readable_by_ai=is_readable)


class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionListSerializer
    permission_classes = [IsAuthenticated]
    queryset = Question.objects.all().order_by('ordering')

    def get_serializer_context(self):
        serializer = QuestionListQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid assistant is required in query parameters'))

        assistant = AssistantService.get(id=serializer.validated_data['assistant_id'])

        context = super().get_serializer_context()
        context['assistant'] = assistant
        return context


class AssistantPlansListView(generics.ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


    def list(self, request, *args, **kwargs):
        assistant = AssistantService.get(id=self.kwargs['pk'])
        assistant_data = OrganizationAssistantSerializer(assistant, context={'request': request}).data
        plans = self.get_queryset()
        plan_data = PlanSerializer(plans, many=True, context={'request': request}).data

        response_data = {
            'assistant': assistant_data,
            'plans': plan_data
        }
        return Response(response_data, status=status.HTTP_200_OK)


class PurchaseAssistantView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PurchaseAssistantSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        assistant = serializer.validated_data['assistant']
        plans = serializer.validated_data['plans']
        duration_days = serializer.validated_data['duration_days']
        utc_offset_minutes = serializer.validated_data['utc_offset_minutes']

        # Get base_url for bot creation after payment
        base_url = request.build_absolute_uri("/").rstrip("/")

        user_assistant = AssistantService.create_or_renew_user_assistant(
            user=request.user,
            processed_by=assistant.organization.owner,
            assistant=assistant,
            plans=plans,
            duration_days=duration_days,
            utc_offset_minutes=utc_offset_minutes,
            base_url=base_url,
        )

        update_assistant_json_task.delay(assistant.organization.id)

        # Bot creation is now triggered AFTER payment in accept_assistant_transaction()
        # Check if "Все включено" plan is selected
        plan_ids = [p.id for p in plans]
        will_create_bot = settings.TELEGRAM_BOT_PLAN_ID in plan_ids

        return Response(
            {
                "message": _("Success"),
                "transaction_id": user_assistant.transaction_id,
                "organization_id": assistant.organization.id,
                "telegram_bot_will_be_created": will_create_bot,
            }
        )


class GetOrCreateChatView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

    def get(self, request, *args, **kwargs):
        serializer = ChatSerializerQueryParam(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = serializer.validated_data.get('user')
        phone = serializer.validated_data.get('phone')
        assistant = serializer.validated_data['assistant']

        if phone:
            # WhatsApp chat - find by phone number
            bot_chat = BotChat.objects.filter(
                organization=assistant.organization,
                platform=BotPlatform.WHATSAPP,
                user_phone=phone,
            ).first()

            if not bot_chat:
                return Response(data={
                    'message': _('Chat not found'),
                    'errors': {'phone': [_('No WhatsApp chat found for this phone number')]}
                }, status=status.HTTP_404_NOT_FOUND)

            # Get or create linked Chat for this BotChat
            chat = Chat.objects.filter(bot_chat=bot_chat).first()
            if not chat:
                chat = Chat.objects.create(
                    assistant=assistant,
                    bot_chat=bot_chat,
                    source=ChatSource.WHATSAPP,
                    user=None,
                )
            created = False
        else:
            # Web chat - find by user
            chat, created = Chat.objects.get_or_create(user=user, assistant=assistant)

        if created:
            CommentService.create_chat_assistant_default_comment(chat=chat, assistant=chat.assistant)

        serializer = self.serializer_class(chat, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatDetailRetrieveView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

    def get(self, request, *args, **kwargs):
        chat = ChatService.get(id=self.kwargs['pk'])
        serializer = self.serializer_class(chat, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AutoChatOrByOrgUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = ChatByOrgUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        chat = serializer.validated_data['chat']
        chat_by_org_user = serializer.validated_data['chat_by_org_user']

        if not OrganizationService.user_can_edit_organization(organization=chat.assistant.organization,
                                                              user=request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})

        ChatService.change_chat_by_org_user_status(chat=chat, chat_by_org_user=chat_by_org_user)

        return Response(data={
            'message': _('Success')
        })


class ToggleAssistantEnableView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = ToggleAssistantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        assistant = serializer.validated_data['assistant']
        is_enabled = serializer.validated_data['is_enabled']

        if not OrganizationService.user_can_edit_organization(organization=assistant.organization,
                                                              user=request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})

        AssistantService.change_assistant_enabled_status(assistant=assistant, is_enabled=is_enabled)

        return Response(data={
            'message': _('Success')
        })


class AssistantChatsListView(generics.ListAPIView):
    serializer_class = ChatListSerializer
    permission_classes = (IsAuthenticated, )

    filter_backends = [SearchFilter]

    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'user__username',
        'bot_chat__user_name',  # Search in Telegram user names
    ]

    def get_object(self):
        return AssistantService.get(id=self.kwargs['pk'])

    def get_queryset(self):
        assistant = self.get_object()
        if not OrganizationService.user_can_edit_organization(organization=assistant.organization,
                                                              user=self.request.user):
            raise PermissionDenied({'message': _('No rights to edit organization')})

        # Create or get web chat for current user
        chat, created = Chat.objects.get_or_create(
            user=self.request.user,
            assistant=assistant,
            defaults={'source': 'web'}
        )
        if created:
            CommentService.create_chat_assistant_default_comment(chat=chat, assistant=chat.assistant)

        # Get all chats (web + telegram) for this assistant
        # Import models for subquery annotations
        from shop.models import Comment  # Web chats store messages in Comment model
        from messenger_bots.models import BotMessage

        # Subqueries for last message (eliminates N+1)
        # Web chats use Comment model (related_name='comments')
        web_last_msg_subquery = Comment.objects.filter(
            chat=OuterRef('pk')
        ).order_by('-created_at').values('text')[:1]

        web_last_msg_time_subquery = Comment.objects.filter(
            chat=OuterRef('pk')
        ).order_by('-created_at').values('created_at')[:1]

        tg_last_msg_subquery = BotMessage.objects.filter(
            chat=OuterRef('bot_chat')
        ).order_by('-created_at').values('text')[:1]

        tg_last_msg_time_subquery = BotMessage.objects.filter(
            chat=OuterRef('bot_chat')
        ).order_by('-created_at').values('created_at')[:1]

        queryset = Chat.objects.filter(assistant=assistant).select_related(
            'user', 'bot_chat', 'assistant', 'assistant__organization'
        ).annotate(
            # Annotate last message text and time (solves N+1 query)
            _web_last_message_text=Subquery(web_last_msg_subquery),
            _web_last_message_time=Subquery(web_last_msg_time_subquery),
            _tg_last_message_text=Subquery(tg_last_msg_subquery),
            _tg_last_message_time=Subquery(tg_last_msg_time_subquery),
        ).annotate(
            is_target_chat=Case(
                When(id=chat.id, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            # For web chats use comments, for telegram chats use bot_chat.messages
            web_last_message_at=Max('comments__created_at'),
            telegram_last_message_at=Max('bot_chat__messages__created_at'),
        ).annotate(
            last_message_created_at=Case(
                When(source='web', then='web_last_message_at'),
                default='telegram_last_message_at',
                output_field=models.DateTimeField()
            )
        ).order_by('-is_target_chat', 'is_read', '-last_message_created_at')

        return queryset



class AssistantChatReadMessages(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        chat = ChatService.get(id=self.kwargs['pk'])

        # Mark messages as read based on chat source
        if chat.source == 'web':
            CommentService.do_read_messages(chat=chat)
        elif chat.bot_chat:
            # Mark Telegram messages as read
            chat.bot_chat.messages.filter(
                sender='user', is_read=False
            ).update(is_read=True)

        # Reset unread counter and mark chat as read
        Chat.objects.filter(id=chat.id).update(
            unread_count=0,
            is_read=True
        )

        return Response(data={
            'message': _('Success')
        })


class GetElevenLabsSignedUrlView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, chat_id):

        agent_id = "agent_3801kfxppx4kf8vvpg5xthybyz3f"

        AI_SERVER_URL = "http://161.35.153.151:8080/bot/api/proxy/elevenlabs/signed-url/"

        try:
            logger.info(f"Proxying signed URL request to AI Server for chat {chat_id}")

            response = requests.get(
                AI_SERVER_URL,
                params={"agent_id": agent_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return Response({
                    "signed_url": data["signed_url"],
                    "agent_id": agent_id
                })
            else:
                logger.error(f"AI Server returned error: {response.text}")
                return Response({"error": "AI Server could not get token"}, status=502)

        except Exception as e:
            logger.error(f"Failed to connect to AI Server: {e}")
            return Response({"error": "AI Server unavailable"}, status=503)
        

        
from project.settings.base import ELEVENLABS_API_KEY2


class ProxyVoicesView(APIView):

    def get(self, request):
        ai_server_url = "http://161.35.153.151:8080/bot/elevenlabs-voices/"

        try:
            response = requests.get(ai_server_url, timeout=20)

            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response({
                    "error": "AI Server returned an error",
                    "details": response.text[:500]
                }, status=response.status_code)

        except Exception as e:
            return Response({"error": f"Failed to connect to AI server: {str(e)}"}, status=500)


class AssistantSettingsUpdateView(generics.UpdateAPIView):
    queryset = Assistant.objects.all()
    serializer_class = AssistantSettingsUpdateSerializer

