from django.urls import reverse
from rest_framework.test import APITestCase

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image
import tempfile

from users.tests.factories import UserFactory, TokenFactory


class WatermarkTestCase(APITestCase):
    def setUp(self):
        self.watermark_url = reverse('v1:watermarked_images')
        self.user = UserFactory(phone_number='123456789')
        self.token = TokenFactory(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token}"}
        self.tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')

        image = Image.new('RGB', (100, 100))
        image.paste((200, 200, 200), [0, 0, image.size[0], image.size[1]])
        image.save(self.tmp_file)

        self.tmp_file.seek(0)

    def test_watermark_image_create(self):

        data = {
            'file': self.tmp_file
        }

        response = self.client.post(self.watermark_url, data, **self.header, format='multipart')

        self.assertEqual(response.status_code, 201)

    def test_watermark_image_invalid(self):

        data = {
            'file': 'file'
        }

        response = self.client.post(self.watermark_url, data, **self.header)

        self.assertEqual(response.status_code, 406)
