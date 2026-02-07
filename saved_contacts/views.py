from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SavedContact
from .serializers import (
    SavedContactSerializer,
    SavedContactCreateSerializer,
    SavedContactUpdateSerializer,
    SavedContactAvatarSerializer,
)
from .services import SavedContactService


class SavedContactListCreateView(ListCreateAPIView):
    """
    List and create saved contacts.

    GET /api/v1/contacts/ - List user's contacts
    POST /api/v1/contacts/ - Create new contact
    """
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SavedContactCreateSerializer
        return SavedContactSerializer

    def get_queryset(self):
        """Return contacts only for the authenticated user."""
        return SavedContactService.get_user_contacts(self.request.user)

    def perform_create(self, serializer):
        """Create contact for the authenticated user."""
        contact = SavedContactService.create(
            user=self.request.user,
            data=serializer.validated_data
        )
        # Re-serialize with the full serializer for response
        serializer.instance = contact


class SavedContactDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a saved contact.

    GET /api/v1/contacts/{id}/ - Get contact details
    PATCH /api/v1/contacts/{id}/ - Update contact
    DELETE /api/v1/contacts/{id}/ - Delete contact
    """
    permission_classes = (IsAuthenticated,)
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return SavedContactUpdateSerializer
        return SavedContactSerializer

    def get_queryset(self):
        """Return contacts only for the authenticated user."""
        return SavedContact.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        """Update contact using service."""
        SavedContactService.update(
            contact=self.get_object(),
            data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        """Delete contact using service."""
        SavedContactService.delete(instance)


class SavedContactAvatarView(APIView):
    """
    Upload or delete contact avatar.

    POST /api/v1/contacts/{id}/avatar/ - Upload avatar
    DELETE /api/v1/contacts/{id}/avatar/ - Delete avatar
    """
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        """Get contact for the authenticated user."""
        return SavedContactService.get(
            pk=self.kwargs['pk'],
            user=self.request.user
        )

    def post(self, request, pk):
        """Upload avatar for contact."""
        contact = self.get_object()
        serializer = SavedContactAvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_contact = SavedContactService.upload_avatar(
            contact=contact,
            file=serializer.validated_data['file']
        )

        return Response(
            SavedContactSerializer(updated_contact).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):
        """Delete avatar from contact."""
        contact = self.get_object()
        updated_contact = SavedContactService.delete_avatar(contact)

        return Response(
            SavedContactSerializer(updated_contact).data,
            status=status.HTTP_200_OK
        )
