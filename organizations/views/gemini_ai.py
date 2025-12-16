from rest_framework.generics import GenericAPIView
from organizations.serializers.gemini_ai import GeminiImageCreateSerializer

# from organizations.services.gemini_ai import GeminiAIService


# class GeminiGenerateImageAPIView(GenericAPIView):
#     serializer_class = GeminiImageCreateSerializer
#     service_class = GeminiAIService

#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(request.data)
#         serializer.is_valid()
#         response = GeminiAIService.generate_from_prompt(**serializer.validated_data)

#         return response
