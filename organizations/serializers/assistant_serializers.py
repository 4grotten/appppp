from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from common.models import File
from common.serializers import ImageSerializer
from organizations.models import Assistant, Organization, Answer, AnswerFile, Question
from organizations.services.assistant_services import AssistantService


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

    class Meta:
        model = Assistant
        fields = ('id', 'organization', 'name', 'gender', 'position', 'image')
        read_only_fields = ('organization', )


class OrganizationAssistantUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Assistant
        fields = ('id', 'organization', 'name', 'gender', 'position', 'image')
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







