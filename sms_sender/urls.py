from django.urls import path

from sms_sender.views import SmsListCreateView

urlpatterns = [
    path('azamat_message_service/', SmsListCreateView.as_view(), name='azamat_message_service'),
]
