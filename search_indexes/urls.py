from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import ShopItemDocumentView

router = DefaultRouter()
router.register('shop/feed', ShopItemDocumentView, basename='shopdocument')

urlpatterns = [
    url(r'^', include(router.urls))
]
