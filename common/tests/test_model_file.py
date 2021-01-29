import tempfile
from django.test import TestCase
from unittest.mock import patch, Mock

from PIL import Image

from common.models import File


class TestModelFile(TestCase):
    def setUp(self):
        self.tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')

        image = Image.new('RGB', (100, 100))
        image.paste((200, 200, 200), [0, 0, image.size[0], image.size[1]])
        image.save(self.tmp_file)

        self.tmp_file.seek(0)

    @patch('urllib.request.urlretrieve')
    def test_model_file_save(self, urlretrieve: Mock):
        urlretrieve.return_value = [self.tmp_file.name, ]

        obj = File.objects.create(image_url='/url/to/file.jpg')

        urlretrieve.assert_called_once_with('/url/to/file.jpg')

        self.assertGreater(obj.file.size, 0)
