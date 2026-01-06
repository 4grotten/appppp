from rest_framework import generics
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import InstagramApi
from .serializers import InstagramApiSerializer

# Create your views here.



class ActiveHikerKeyView(generics.RetrieveAPIView):

    serializer_class = InstagramApiSerializer

    def get_object(self):
        obj = InstagramApi.objects.filter(is_active=True).order_by('-created_at').first()
        if not obj:
            self.permission_denied(self.request, message="No active keys found")
        return obj