from django.urls import path
from .views import ActiveHikerKeyView

urlpatterns = [
    path('config/hiker-key/', ActiveHikerKeyView.as_view(), name='get-hiker-key'),
]