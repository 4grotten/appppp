from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _

from sms_sender.models import SmsModel
from sms_sender.serializers import SmsSerializer, SmsPostSerializer
from rest_framework.response import Response


class SmsListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SmsSerializer

    def get_queryset(self):
        return SmsModel.objects.exclude(status='success')

    def post(self, request, *args, **kwargs):
        serializer = SmsPostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        sms_status = serializer.validated_data['sms_status']
        sms_id = serializer.validated_data['sms_id']
        SmsModel.objects.filter(id=sms_id).update(status=sms_status)
        data = SmsSerializer(SmsModel.objects.get(id=sms_id)).data
        return Response(data, status=status.HTTP_200_OK)
