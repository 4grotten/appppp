from django.urls import path, include

from messenger.views import FolderListCreateAPIView, FolderUpdateAPIView

folders_url = [
    path(
        "messenger/folders/",
        FolderListCreateAPIView.as_view(),
        name="folders",
    ),
    path(
        "messenger/folders/<int:pk>/",
        FolderUpdateAPIView.as_view(),
        name="folder",
    ),
]
