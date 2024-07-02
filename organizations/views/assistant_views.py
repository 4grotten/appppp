from django.db.models import Max
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException
from common.pagination import GeneralPagination
from organizations.models import Answer, AnswerFile, Question, Assistant, Plan, Chat, ChatMessage
from organizations.serializers.assistant_serializers import AssistantCreateSerializer, \
    OrganizationAssistantAnswerCreateSerializer, AnswerFileSerializer, OrganizationAssistantAnswerRetrieveSerializer, \
    QuestionListSerializer, QuestionListQueryParamSerializer, OrganizationAssistantSerializer, \
    PlanSerializer, AssistantSerializer, PurchaseAssistantSerializer, MessageCreateSerializer, ChatSerializerQueryParam, \
    ChatSerializer, ChatMessageSerializer, ChatListSerializer, ChatByOrgUserSerializer, ToggleAssistantSerializer
from organizations.services.assistant_services import AssistantService, AnswerService, ChatService, ChatMessageService
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
        plan_data = PlanSerializer(plans, many=True).data

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

        user_assistant = AssistantService.create_or_renew_user_assistant(user=request.user,
                                                                         processed_by=assistant.organization.owner,
                                                                         assistant=assistant, plans=plans,
                                                                         duration_days=duration_days,
                                                                         utc_offset_minutes=utc_offset_minutes)

        return Response(
            {
                "message": _("Success"),
                "transaction_id": user_assistant.transaction_id
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

        user = serializer.validated_data['user']
        assistant = serializer.validated_data['assistant']

        chat, created = Chat.objects.get_or_create(user=user, assistant=assistant)

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

    def get_object(self):
        return AssistantService.get(id=self.kwargs['pk'])

    def get_queryset(self):
        assistant = self.get_object()
        return Chat.objects.filter(assistant=assistant).annotate(
            last_message_created_at=Max('chat_messages__created_at')
        ).order_by('-last_message_created_at')



class AssistantChatReadMessages(APIView):

    def post(self, request, *args, **kwargs):
        chat = ChatService.get(id=self.kwargs['pk'])

        CommentService.do_read_messages(chat=chat)

        return Response(data={
            'message': _('Success')
        })