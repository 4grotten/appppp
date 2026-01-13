from django.core.management.base import BaseCommand
from organizations.models import Organization
from shop.services.assistant_data_service import AssistantDataService


class Command(BaseCommand):
    help = "Генерирует JSON файлы для 10 активных организаций (для теста)"

    def handle(self, *args, **options):
        organizations = Organization.objects.filter(assistant__isnull=False)

        total_checked = 0
        files_created = 0
        limit = 10

        self.stdout.write(f"Начинаем поиск активных ассистентов...")

        for org in organizations:
            if files_created >= limit:
                break

            total_checked += 1

            if AssistantDataService.is_assistant_active(org):
                try:
                    AssistantDataService.update_organization_json(org)
                    files_created += 1
                    self.stdout.write(self.style.SUCCESS(f"[{files_created}/{limit}] OK: {org.title}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка при создании {org.title}: {e}"))

            # else:
            #    self.stdout.write(f"Skipped (inactive): {org.title}")

        self.stdout.write(self.style.WARNING(f"Проверено организаций: {total_checked}"))
        self.stdout.write(self.style.SUCCESS(f"Успешно создано файлов: {files_created}"))