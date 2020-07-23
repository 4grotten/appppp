from organizations.models import Banner, Organization


class BannerService:
    @classmethod
    def get_banners(cls, organization: Organization = None):
        if organization is not None:
            return Banner.objects.filter(host_organization=organization).order_by('-updated_at')
        return Banner.objects.filter(host_organization__isnull=True).order_by('-updated_at')
