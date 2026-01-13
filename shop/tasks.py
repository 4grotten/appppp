from celery import shared_task
from .models import Organization
from .services.assistant_data_service import AssistantDataService

@shared_task
def update_assistant_json_task(organization_id):
    try:
        organization = Organization.objects.get(id=organization_id)
        AssistantDataService.update_organization_json(organization)
    except Organization.DoesNotExist:
        pass



@shared_task
def cleanup_expired_assistants_files():
    organizations = Organization.objects.filter(assistant__isnull=False)
    for org in organizations:
        if not AssistantDataService.is_assistant_active(org):
             AssistantDataService.delete_organization_json(org)