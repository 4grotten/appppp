from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from search_indexes.views.item_views import SuggestSearchDocumentView

from search_indexes.views.organization_views import OrganizationDocumentView

router = DefaultRouter()
router.register('homepage/search', OrganizationDocumentView, basename='homepage_search')
# router.register('search/item', SuggestSearchDocumentView, basename='search/item')
# router.register('shop/organization_items', ShopOrgnizationItemDocumentView, basename='organization_items')
# router.register('shop/feed', ShopItemDocumentView, basename='shop_feed')

urlpatterns = [
    url(r'^', include(router.urls)),
]
