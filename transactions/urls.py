from django.urls import path

from transactions.views.stat_views import PartnersTotalStatsView
from transactions.views.transaction_views import (
    TransactionCompleteView, TransactionPreprocessView, TransactionOrganizationsView,
    TransactionUserTotalsView
)

urlpatterns = [
    path('transactions/preprocess/', TransactionPreprocessView.as_view(), name='transaction_preprocess'),
    path('transactions/complete/', TransactionCompleteView.as_view(), name='transaction_complete'),

    path('statistics/totals/', TransactionUserTotalsView.as_view(), name='user_totals'),
    path('statistics/organizations/', TransactionOrganizationsView.as_view(), name='transaction_organizations'),

    path('statistics/<int:pk>/partners/', PartnersTotalStatsView.as_view(), name='partners_totals')
]
