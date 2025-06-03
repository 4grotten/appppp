from django.urls import path, include

from applications.views import UserAppListCreateView, ToggleUserAppView

user_app_urls = [
    path('applications/', UserAppListCreateView.as_view(), name='user_applications'),
    path('applications/<int:pk>/toggle/', ToggleUserAppView.as_view(), name='toggle_user_app')
]
urlpatterns = [
    path('', include(user_app_urls)),
]

