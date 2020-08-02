from django.urls import path

from transactions.views.stat_views import PartnersTotalStatsView, OrganizationTotalsView
from transactions.views.transaction_views import (
    TransactionCompleteView, TransactionPreprocessView, UserTransactionOrganizationView,
    UserTotalsView, UserTransactionsListView, UserTransactionDetailView,
    OrganizationTransactionListView, OrganizationTransactionDetailView
)

urlpatterns = [
    path('transactions/', OrganizationTransactionListView.as_view(), name='organization_transactions'),
    path('transactions/<int:pk>/', OrganizationTransactionDetailView.as_view(), name='organization_transaction_detail'),

    path('transactions/preprocess/', TransactionPreprocessView.as_view(), name='transaction_preprocess'),
    path('transactions/complete/', TransactionCompleteView.as_view(), name='transaction_complete'),

    path('statistics/totals/', UserTotalsView.as_view(), name='user_totals'),
    path('statistics/transactions/', UserTransactionsListView.as_view(), name='user_transactions'),
    path('statistics/transactions/<int:pk>/', UserTransactionDetailView.as_view(), name='user_transaction_detail'),
    path('statistics/organizations/', UserTransactionOrganizationView.as_view(), name='transaction_organizations'),

    path('statistics/<int:pk>/partners_totals/', PartnersTotalStatsView.as_view(), name='partners_totals'),
    path('statistics/<int:pk>/totals/', OrganizationTotalsView.as_view(), name='organization_totals'),
]
