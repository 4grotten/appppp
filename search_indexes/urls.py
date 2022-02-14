from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from search_indexes.views.item_views import ShopItemDocumentView, ShopOrgnizationItemDocumentView

from search_indexes.views.organization_views import OrganizationDocumentView

router = DefaultRouter()
router.register('homepage/search', OrganizationDocumentView, basename='organizationdocument')
router.register('shop/organization_items', ShopOrgnizationItemDocumentView, basename='shoporgdocument')
# router.register('shop/feed', ShopItemDocumentView, basename='shopdocument')

urlpatterns = [
    url(r'^', include(router.urls)),
]
