from django.urls import path

from .views import (
    SavedContactListCreateView,
    SavedContactDetailView,
    SavedContactAvatarView,
)

urlpatterns = [
    path('', SavedContactListCreateView.as_view(), name='contact-list-create'),
    path('<uuid:pk>/', SavedContactDetailView.as_view(), name='contact-detail'),
    path('<uuid:pk>/avatar/', SavedContactAvatarView.as_view(), name='contact-avatar'),
]
