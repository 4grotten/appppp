from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException
from organizations.models import Answer, AnswerFile, Question
from organizations.serializers.assistant_serializers import AssistantCreateSerializer, \
    OrganizationAssistantAnswerCreateSerializer, AnswerFileSerializer, OrganizationAssistantAnswerRetrieveSerializer, \
    QuestionListSerializer, QuestionListQueryParamSerializer
from organizations.services.assistant_services import AssistantService, AnswerService
from organizations.services.organization_services import OrganizationService


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

        serializer.save()

        return Response(data={"message": "Assistant successfully created"}, status=status.HTTP_201_CREATED)


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



