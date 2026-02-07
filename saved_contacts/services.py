import uuid
from typing import Any, Dict, Optional

from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from common.exceptions import IntegrityException, ObjectNotFoundException
from common.models import File
from .models import SavedContact


class SavedContactService:
    """Service class for SavedContact operations."""

    model = SavedContact

    @classmethod
    def get(cls, **filters) -> SavedContact:
        """Get a single SavedContact by filters."""
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Contact not found'))

    @classmethod
    def filter(cls, **filters):
        """Filter SavedContacts."""
        return cls.model.objects.filter(**filters)

    @classmethod
    def get_user_contacts(cls, user):
        """Get all contacts for a specific user."""
        return cls.model.objects.filter(user=user).order_by('-created_at')

    @classmethod
    def create(cls, user, data: Dict[str, Any]) -> SavedContact:
        """
        Create a new SavedContact.

        Args:
            user: The user who owns the contact
            data: Contact data dictionary

        Returns:
            Created SavedContact instance
        """
        try:
            # Ensure payment_methods and social_links have valid IDs
            payment_methods = data.get('payment_methods', [])
            social_links = data.get('social_links', [])

            # Generate IDs if missing
            for pm in payment_methods:
                if not pm.get('id'):
                    pm['id'] = str(uuid.uuid4())

            for sl in social_links:
                if not sl.get('id'):
                    sl['id'] = str(uuid.uuid4())

            contact = cls.model.objects.create(
                user=user,
                full_name=data['full_name'],
                phone=data.get('phone'),
                email=data.get('email'),
                company=data.get('company'),
                position=data.get('position'),
                avatar_id=data.get('avatar_id'),
                notes=data.get('notes'),
                payment_methods=payment_methods,
                social_links=social_links,
            )
            return contact
        except IntegrityError as e:
            raise IntegrityException(_('Error while creating contact'))

    @classmethod
    def update(cls, contact: SavedContact, data: Dict[str, Any]) -> SavedContact:
        """
        Update an existing SavedContact.

        Args:
            contact: SavedContact instance to update
            data: Updated data dictionary

        Returns:
            Updated SavedContact instance
        """
        try:
            # Update fields if provided
            if 'full_name' in data:
                contact.full_name = data['full_name']
            if 'phone' in data:
                contact.phone = data['phone']
            if 'email' in data:
                contact.email = data['email']
            if 'company' in data:
                contact.company = data['company']
            if 'position' in data:
                contact.position = data['position']
            if 'notes' in data:
                contact.notes = data['notes']
            if 'avatar_id' in data:
                contact.avatar_id = data['avatar_id'] if data['avatar_id'] else None

            # Handle payment_methods - generate IDs if missing
            if 'payment_methods' in data:
                payment_methods = data['payment_methods']
                for pm in payment_methods:
                    if not pm.get('id'):
                        pm['id'] = str(uuid.uuid4())
                contact.payment_methods = payment_methods

            # Handle social_links - generate IDs if missing
            if 'social_links' in data:
                social_links = data['social_links']
                for sl in social_links:
                    if not sl.get('id'):
                        sl['id'] = str(uuid.uuid4())
                contact.social_links = social_links

            contact.save()
            return contact
        except IntegrityError:
            raise IntegrityException(_('Error while updating contact'))

    @classmethod
    def delete(cls, contact: SavedContact) -> None:
        """
        Delete a SavedContact.

        Args:
            contact: SavedContact instance to delete
        """
        contact.delete()

    @classmethod
    def upload_avatar(cls, contact: SavedContact, file) -> SavedContact:
        """
        Upload and set avatar for a contact.

        Args:
            contact: SavedContact instance
            file: Uploaded file object

        Returns:
            Updated SavedContact instance
        """
        try:
            # Create File object for the avatar
            file_obj = File.objects.create(
                file=file
            )

            # Delete old avatar if exists
            if contact.avatar:
                old_avatar = contact.avatar
                contact.avatar = None
                contact.save()
                old_avatar.delete()

            # Set new avatar
            contact.avatar = file_obj
            contact.save()

            return contact
        except Exception as e:
            raise IntegrityException(_('Error while uploading avatar'))

    @classmethod
    def delete_avatar(cls, contact: SavedContact) -> SavedContact:
        """
        Delete avatar from a contact.

        Args:
            contact: SavedContact instance

        Returns:
            Updated SavedContact instance
        """
        if contact.avatar:
            old_avatar = contact.avatar
            contact.avatar = None
            contact.save()
            old_avatar.delete()

        return contact
