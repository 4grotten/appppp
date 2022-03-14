from django.urls import path

from sms_sender.views import SmsGetPostView

urlpatterns = [
    path('azamat_message_service/', SmsGetPostView.as_view(), name='azamat_message_service'),
]
