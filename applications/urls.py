from django.urls import path, include

from applications.views import UserAppCreateView

user_app_urls = [
    path('applications/', UserAppCreateView.as_view(), name='user_applications'),
]
urlpatterns = [
    path('', include(user_app_urls)),
]

