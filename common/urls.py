from django.urls import path

from common.views import (
    ImageCreateView, CountriesListView, CountryCitySearchView, WatermarkImageCreateView, ImageCreateFromUrlView,
    YoutubeEmbedView, GetLatestAppVersion, LanguagesList, SendEmailToApofiz, ShadowBanStatus
)

urlpatterns = [
    path('files/', ImageCreateView.as_view(), name='images'),
    path('save_image_from_url/', ImageCreateFromUrlView.as_view(), name='image_from_url'),
    path('watermarked_images/', WatermarkImageCreateView.as_view(), name='watermarked_images'),
    path('countries/', CountriesListView.as_view(), name='countries'),
    path('countries_and_cities/', CountryCitySearchView.as_view(), name='countries_cities_search'),
    path('youtube_embed/', YoutubeEmbedView.as_view(), name='youtube_embed'),
    path('app_version/<slug:device>/', GetLatestAppVersion.as_view(), name='latest_app_version'),
    path('languages/', LanguagesList.as_view(), name='languages_list'),
    path('request_from_shadow_ban/<int:pk>/', SendEmailToApofiz.as_view(), name='email_to_apofiz'),
    path('shadow_ban_status/<int:pk>/', ShadowBanStatus.as_view(), name='shadow_ban_status')
]
