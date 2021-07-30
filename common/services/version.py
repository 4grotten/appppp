from common.models import Version


class VersionService:

    @classmethod
    def check_version_in_database(cls, data):
        has_version = Version.objects.filter(device=data['device'], version=data['version']).exists()
        return has_version

    @classmethod
    def check_if_need_update(cls, device, version):
        required_to_update = Version.objects.filter(device=device,
                                                    required_to_update=True).values_list('version', flat=True)
        print(required_to_update)
        return
