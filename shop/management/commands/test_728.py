from django.core.management.base import BaseCommand
from django.utils import timezone
from organizations.models import Organization, UserAssistant
from shop.services.assistant_data_service import AssistantDataService


class Command(BaseCommand):
    help = "Детальная проверка организации ID 728"

    def handle(self, *args, **options):
        org_id = 728
        print(f"\n🔍 ПРОВЕРКА ОРГАНИЗАЦИИ {org_id}")
        print(f"🕒 Время сервера: {timezone.now()}")

        # 1. Ищем организацию
        try:
            org = Organization.objects.get(id=org_id)
            print(f"✅ Организация найдена: '{org.title}'")
        except Organization.DoesNotExist:
            print(f"❌ Организация с ID {org_id} не существует!")
            return

        # 2. Ищем ассистента
        if not hasattr(org, 'assistant'):
            print(f"❌ У организации нет связанного Assistant (OneToOneField пусто).")
            return

        assistant = org.assistant
        print(f"✅ Ассистент найден: ID {assistant.id}, Name: '{assistant.name}'")

        # 3. Смотрим таблицу UserAssistant (подписки)
        user_assistants = UserAssistant.objects.filter(assistant=assistant)

        if not user_assistants.exists():
            print(f"❌ В таблице UserAssistant нет записей для этого ассистента.")
            print(f"   (Возможно, подписка была, но запись удалена?)")
        else:
            print(f"🔎 Найдено записей в UserAssistant: {user_assistants.count()}")

            for ua in user_assistants:
                print(f"   --- Запись ID {ua.id} ---")
                print(f"   User: {ua.user}")
                print(f"   is_active: {ua.is_active}  <-- {'🟢 OK' if ua.is_active else '🔴 FAIL'}")
                print(f"   active_until: {ua.active_until}")

                # Проверка даты
                if ua.active_until:
                    if ua.active_until > timezone.now():
                        print(f"   Время: 🟢 Действует (В будущем)")
                    else:
                        print(f"   Время: 🔴 Истекло (В прошлом)")
                else:
                    print(f"   Время: 🔴 None (Не установлено)")

        # 4. Проверяем, что скажет наш Сервис
        print("-" * 30)
        is_active_service = AssistantDataService.is_assistant_active(org)
        print(f"🤖 Вердикт сервиса (is_assistant_active): {is_active_service}")

        if is_active_service:
            print("🚀 Пытаемся создать JSON...")
            try:
                AssistantDataService.update_organization_json(org)
                # Проверим, создался ли файл
                file_path = AssistantDataService._get_file_path(org)
                if file_path.exists():
                    print(f"✅ УСПЕХ! Файл создан: {file_path}")
                    print(f"   Размер файла: {file_path.stat().st_size} байт")
                else:
                    print(f"⚠️ Странно: Ошибок нет, но файла тоже нет.")
            except Exception as e:
                print(f"❌ Ошибка при генерации JSON: {e}")
        else:
            print("⛔ Генерация отменена, так как сервис считает подписку неактивной.")