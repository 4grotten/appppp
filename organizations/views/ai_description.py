import requests
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.models import ChatGPTSettings
from organizations.serializers.assistant_serializers import CreateDescriptionSerializer


class GenerateDescriptionChatGPTAPIView(GenericAPIView):
    serializer_class = CreateDescriptionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 0. Получаем настройки ChatGPT из базы данных
        chatgpt_settings = ChatGPTSettings.get_settings()

        if not chatgpt_settings.is_active:
            return Response(
                {"error": "ChatGPT integration is disabled"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        api_key = chatgpt_settings.api_key
        if not api_key:
            return Response(
                {"error": "ChatGPT API key is not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # 1. Валидация входных данных
        # Временно отключено для тестирования - прокси недоступен
        # if settings.DEBUG:
        #     proxy_url = f"socks5://{settings.PROXY_USER}:{settings.PROXY_PASS}@{settings.PROXY_HOST}:{settings.PROXY_PORT}"
        #     proxies = {"http": proxy_url, "https": proxy_url}
        # else:
        #     proxies = None
        proxies = None  # Прокси отключен для тестирования

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 2. Получение языка из заголовка Accept-Language
        # Пример заголовка: "ru-RU,ru;q=0.9,en-US;q=0.8"
        accept_language = request.headers.get("Accept-Language", "ru")

        # Берем только первую часть до запятой (самый приоритетный язык)
        # Например, из "ru-RU,ru;q=0.9" получим "ru-RU"
        language = accept_language.split(",")[0]

        name = data.get("name", "Unknown Organization")  # type: ignore
        description = data.get("description", "")  # type: ignore

        # 3. Подготовка запроса к OpenAI
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # ChatGPT отлично понимает коды языков (ru, en-US, de),
        # поэтому "Target Language: ru-RU" сработает корректно.
        system_prompt = (
            f"Act as a professional SMM copywriter and brand specialist. "
            f"Task: Create a professional and engaging description for an organization's media profile. "
            f"Target Language: {language}.\n\n"
            "Guidelines:\n"
            "1. Tone: Professional yet approachable, trustworthy, and modern.\n"
            "2. Length: Medium (3-5 sentences).\n"
            "3. Content: If details are provided, rewrite them to be catchy and don't use hashtags. If missing, infer likely industry from the Name.\n"
        )

        user_prompt = (
            f"Input Data:\n"
            f"- Organization Name: {name}\n"
            f"- Key Details/Draft: {description if description else 'Not specified, generate based on name.'}"
        )

        payload = {
            "model": chatgpt_settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": chatgpt_settings.temperature,
        }

        try:
            # 4. Отправка запроса
            print(f"\n{'='*60}")
            print("📤 ОТПРАВКА К CHATGPT API")
            print(f"{'='*60}")
            print(f"Model: {payload['model']}")
            print(f"Temperature: {payload['temperature']}")
            print(f"Language: {language}")
            print(f"Input Name: {name}")
            print(f"Input Description: {description[:100] if description else 'None'}...")
            print(f"{'='*60}\n")

            response = requests.post(
                url, json=payload, headers=headers, proxies=proxies, timeout=30
            )
            response.raise_for_status()

            response_json = response.json()
            ai_content = response_json["choices"][0]["message"]["content"]

            # Логируем ответ
            print(f"\n{'='*60}")
            print("📥 ОТВЕТ ОТ CHATGPT API")
            print(f"{'='*60}")
            print(f"Status: {response.status_code}")
            print(f"Response Length: {len(ai_content)} chars")
            print(f"Generated Content Preview: {ai_content[:150]}...")
            print(f"{'='*60}\n")

            return Response({"result": ai_content}, status=200)

        except requests.exceptions.RequestException as e:
            # Можно добавить логирование (logger.error(e))
            print(f"\n❌ ОШИБКА ChatGPT API: {e}")
            return Response(
                {"error": "Failed to connect to AI provider"},
                status=503,
            )
