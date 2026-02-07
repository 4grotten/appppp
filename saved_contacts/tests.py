import uuid
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from common.exceptions import ObjectNotFoundException
from .models import SavedContact
from .services import SavedContactService

User = get_user_model()


def create_test_image():
    """Create a test image for avatar upload tests."""
    file = BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'PNG')
    file.seek(0)
    return SimpleUploadedFile(
        name='test.png',
        content=file.read(),
        content_type='image/png'
    )


class SavedContactModelTest(TestCase):
    """Tests for SavedContact model."""

    def setUp(self):
        self.user = User.objects.create(phone_number='+971501234567')

    def test_create_contact_minimal(self):
        """Test creating contact with minimal fields."""
        contact = SavedContact.objects.create(
            user=self.user,
            full_name='John Doe'
        )
        self.assertEqual(contact.full_name, 'John Doe')
        self.assertEqual(contact.user, self.user)
        self.assertIsInstance(contact.id, uuid.UUID)
        self.assertIsNotNone(contact.created_at)
        self.assertIsNotNone(contact.updated_at)

    def test_create_contact_full(self):
        """Test creating contact with all fields."""
        payment_methods = [
            {'id': '1', 'type': 'card', 'label': 'Main Card', 'value': '4111111111111111'}
        ]
        social_links = [
            {'id': '1', 'networkId': 'linkedin', 'networkName': 'LinkedIn', 'url': 'https://linkedin.com/in/johndoe'}
        ]

        contact = SavedContact.objects.create(
            user=self.user,
            full_name='John Doe',
            phone='+971501234567',
            email='john@example.com',
            company='Acme Inc',
            position='CEO',
            notes='Important client',
            payment_methods=payment_methods,
            social_links=social_links,
        )

        self.assertEqual(contact.phone, '+971501234567')
        self.assertEqual(contact.email, 'john@example.com')
        self.assertEqual(contact.company, 'Acme Inc')
        self.assertEqual(contact.position, 'CEO')
        self.assertEqual(contact.notes, 'Important client')
        self.assertEqual(len(contact.payment_methods), 1)
        self.assertEqual(len(contact.social_links), 1)

    def test_str_representation(self):
        """Test string representation."""
        contact = SavedContact.objects.create(
            user=self.user,
            full_name='John Doe'
        )
        self.assertIn('John Doe', str(contact))

    def test_avatar_url_none_when_no_avatar(self):
        """Test avatar_url returns None when no avatar."""
        contact = SavedContact.objects.create(
            user=self.user,
            full_name='John Doe'
        )
        self.assertIsNone(contact.avatar_url)


class SavedContactServiceTest(TestCase):
    """Tests for SavedContactService."""

    def setUp(self):
        self.user = User.objects.create(phone_number='+971501234567')
        self.other_user = User.objects.create(phone_number='+971501234568')

    def test_create_contact(self):
        """Test creating contact via service."""
        data = {
            'full_name': 'Jane Doe',
            'phone': '+971509876543',
            'email': 'jane@example.com',
        }
        contact = SavedContactService.create(self.user, data)

        self.assertEqual(contact.full_name, 'Jane Doe')
        self.assertEqual(contact.phone, '+971509876543')
        self.assertEqual(contact.user, self.user)

    def test_create_contact_generates_ids(self):
        """Test that create generates IDs for payment_methods and social_links."""
        data = {
            'full_name': 'Test',
            'payment_methods': [
                {'type': 'card', 'label': 'Card', 'value': '123'}
            ],
            'social_links': [
                {'networkId': 'fb', 'networkName': 'Facebook', 'url': 'https://fb.com/test'}
            ]
        }
        contact = SavedContactService.create(self.user, data)

        self.assertTrue(contact.payment_methods[0].get('id'))
        self.assertTrue(contact.social_links[0].get('id'))

    def test_update_contact(self):
        """Test updating contact via service."""
        contact = SavedContact.objects.create(
            user=self.user,
            full_name='Original Name'
        )

        updated = SavedContactService.update(contact, {'full_name': 'New Name'})
        self.assertEqual(updated.full_name, 'New Name')

    def test_delete_contact(self):
        """Test deleting contact via service."""
        contact = SavedContact.objects.create(
            user=self.user,
            full_name='To Delete'
        )
        contact_id = contact.id

        SavedContactService.delete(contact)
        self.assertFalse(SavedContact.objects.filter(id=contact_id).exists())

    def test_get_contact_not_found(self):
        """Test get raises exception for non-existent contact."""
        with self.assertRaises(ObjectNotFoundException):
            SavedContactService.get(id=uuid.uuid4())

    def test_get_user_contacts(self):
        """Test getting contacts for specific user."""
        SavedContact.objects.create(user=self.user, full_name='Contact 1')
        SavedContact.objects.create(user=self.user, full_name='Contact 2')
        SavedContact.objects.create(user=self.other_user, full_name='Other Contact')

        contacts = SavedContactService.get_user_contacts(self.user)
        self.assertEqual(contacts.count(), 2)


class SavedContactAPITest(APITestCase):
    """API tests for saved contacts."""

    def setUp(self):
        self.user = User.objects.create(phone_number='+971501234567')
        self.other_user = User.objects.create(phone_number='+971501234568')

        # Create token for authentication
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create test contact
        self.contact = SavedContact.objects.create(
            user=self.user,
            full_name='Test Contact',
            phone='+971509999999'
        )

    def test_list_contacts(self):
        """Test listing user's contacts."""
        response = self.client.get('/api/v1/contacts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Uses GeneralPagination with 'list' key
        self.assertEqual(len(response.data['list']), 1)

    def test_list_contacts_only_own(self):
        """Test that user can only see their own contacts."""
        SavedContact.objects.create(
            user=self.other_user,
            full_name='Other Contact'
        )
        response = self.client.get('/api/v1/contacts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['list']), 1)
        self.assertEqual(response.data['list'][0]['full_name'], 'Test Contact')

    def test_create_contact(self):
        """Test creating a new contact."""
        data = {
            'full_name': 'New Contact',
            'phone': '+971508888888',
            'email': 'new@example.com',
            'company': 'New Company',
        }
        response = self.client.post('/api/v1/contacts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['full_name'], 'New Contact')
        self.assertTrue(SavedContact.objects.filter(full_name='New Contact').exists())

    def test_create_contact_with_payment_methods(self):
        """Test creating contact with payment methods."""
        data = {
            'full_name': 'Contact With Payment',
            'payment_methods': [
                {'id': 'pm1', 'type': 'card', 'label': 'Visa', 'value': '4111111111111111'},
                {'id': 'pm2', 'type': 'iban', 'label': 'IBAN', 'value': 'AE123456789'},
            ]
        }
        response = self.client.post('/api/v1/contacts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['payment_methods']), 2)

    def test_create_contact_with_social_links(self):
        """Test creating contact with social links."""
        data = {
            'full_name': 'Contact With Social',
            'social_links': [
                {
                    'id': 'sl1',
                    'networkId': 'linkedin',
                    'networkName': 'LinkedIn',
                    'url': 'https://linkedin.com/in/test'
                }
            ]
        }
        response = self.client.post('/api/v1/contacts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['social_links']), 1)

    def test_retrieve_contact(self):
        """Test retrieving a specific contact."""
        response = self.client.get(f'/api/v1/contacts/{self.contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Test Contact')

    def test_retrieve_contact_not_found(self):
        """Test retrieving non-existent contact."""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/v1/contacts/{fake_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_other_users_contact(self):
        """Test that user cannot retrieve other user's contact."""
        other_contact = SavedContact.objects.create(
            user=self.other_user,
            full_name='Other Contact'
        )
        response = self.client.get(f'/api/v1/contacts/{other_contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_contact(self):
        """Test updating a contact."""
        data = {
            'full_name': 'Updated Name',
            'company': 'Updated Company',
        }
        response = self.client.patch(f'/api/v1/contacts/{self.contact.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.contact.refresh_from_db()
        self.assertEqual(self.contact.full_name, 'Updated Name')
        self.assertEqual(self.contact.company, 'Updated Company')

    def test_delete_contact(self):
        """Test deleting a contact."""
        response = self.client.delete(f'/api/v1/contacts/{self.contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SavedContact.objects.filter(id=self.contact.id).exists())

    def test_delete_other_users_contact(self):
        """Test that user cannot delete other user's contact."""
        other_contact = SavedContact.objects.create(
            user=self.other_user,
            full_name='Other Contact'
        )
        response = self.client.delete(f'/api/v1/contacts/{other_contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(SavedContact.objects.filter(id=other_contact.id).exists())

    def test_unauthenticated_access(self):
        """Test that unauthenticated access is denied."""
        self.client.credentials()  # Remove auth
        response = self.client.get('/api/v1/contacts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_contact_validation(self):
        """Test validation on create."""
        # Missing required field
        data = {'phone': '+971508888888'}
        response = self.client.post('/api/v1/contacts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_payment_method_type(self):
        """Test validation of invalid payment method type."""
        data = {
            'full_name': 'Test',
            'payment_methods': [
                {'id': 'pm1', 'type': 'invalid_type', 'label': 'Test', 'value': '123'}
            ]
        }
        response = self.client.post('/api/v1/contacts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_social_link_url(self):
        """Test validation of invalid social link URL."""
        data = {
            'full_name': 'Test',
            'social_links': [
                {'id': 'sl1', 'networkId': 'fb', 'networkName': 'Facebook', 'url': 'not-a-url'}
            ]
        }
        response = self.client.post('/api/v1/contacts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SavedContactAvatarAPITest(APITestCase):
    """API tests for avatar upload/delete."""

    def setUp(self):
        self.user = User.objects.create(phone_number='+971501234567')
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.contact = SavedContact.objects.create(
            user=self.user,
            full_name='Test Contact'
        )

    def test_upload_avatar(self):
        """Test uploading avatar for contact."""
        image = create_test_image()
        response = self.client.post(
            f'/api/v1/contacts/{self.contact.id}/avatar/',
            {'file': image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contact.refresh_from_db()
        self.assertIsNotNone(self.contact.avatar)
        self.assertIsNotNone(response.data['avatar_url'])

    def test_delete_avatar(self):
        """Test deleting avatar from contact."""
        # First upload an avatar
        from common.models import File
        avatar = File.objects.create(file=create_test_image())
        self.contact.avatar = avatar
        self.contact.save()

        response = self.client.delete(f'/api/v1/contacts/{self.contact.id}/avatar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.contact.refresh_from_db()
        self.assertIsNone(self.contact.avatar)
        self.assertIsNone(response.data['avatar_url'])
