from organizations.models import Banner, Organization


class BannerService:
    @classmethod
    def get_banners(cls, organization: Organization):
        return Banner.objects.filter(host_organization=organization).order_by('-updated_at')
