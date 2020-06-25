from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser

from .models import File
from .serializers import FileSerializer


class FileCreateView(CreateAPIView):
    parser_classes = (MultiPartParser,)
    serializer_class = FileSerializer
    queryset = File.objects.all()
