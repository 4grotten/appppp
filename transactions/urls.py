from django.urls import path

from transactions.views.stat_views import (
    PartnersTotalStatsView, OrganizationTotalsView, OrganizationTransactionCalendarView,
)
from transactions.views.transaction_views import (
    TransactionCompleteView, TransactionPreprocessView, UserTransactionOrganizationView, UserTotalsView,
    UserTransactionsListView, UserTransactionDetailView, OrganizationTransactionListView,
    OrganizationTransactionRetrieveDestroyView, UserUnprocessedTransactionCountView, UserSaleTotalsView,
    UserSaleTransactionsListView, UserSaleTransactionOrganizationView, OnlineTransactionCompleteView,
    OrganizationUsersTransactionView, OnlineBookingTransactionCompleteView,
    OrganizationBookingTransactionRetrieveDestroyView, RentPaymentRejectView, RentPaymentAcceptView,
    TransactionBookingPreprocessView, TransactionBookingCompleteView
)

urlpatterns = [
    path('transactions/', OrganizationTransactionListView.as_view(), name='organization_transactions'),
    path('transactions/<int:pk>/', OrganizationTransactionRetrieveDestroyView.as_view(),
         name='organization_transaction_detail'),
    path('transactions/<int:pk>/booking/', OrganizationBookingTransactionRetrieveDestroyView.as_view(),
         name='organization_booking_transaction_detail'),

    path('transactions/preprocess/', TransactionPreprocessView.as_view(), name='transaction_preprocess'),
    path('transactions/complete/', TransactionCompleteView.as_view(), name='transaction_complete'),
    path('transactions/organizations/<int:pk>/users/', OrganizationUsersTransactionView.as_view(),
         name='transactions_organizations_users'),
    path('onlineTransactions/complete/', OnlineTransactionCompleteView.as_view(), name='online_transaction_complete'),

    path('transactions/preprocess/booking/<int:pk>/', TransactionBookingPreprocessView.as_view(),
         name='transaction_booking_preprocess'),
    path('transactions/complete/booking/', TransactionBookingCompleteView.as_view(), name='transaction_booking_complete'),
    path('onlineBookingTransactions/complete/', OnlineBookingTransactionCompleteView.as_view(),
         name='online_booking_transaction_complete'),
    path('transactions/payment/accept/', RentPaymentAcceptView.as_view(), name='user_transaction_reject'),
    path('transactions/<int:pk>/reject/', RentPaymentRejectView.as_view(), name='user_transaction_reject'),

    path('statistics/totals/', UserTotalsView.as_view(), name='user_totals'),
    path('statistics/saleTotals/', UserSaleTotalsView.as_view(), name='user_sale_totals'),
    path('statistics/transactions/', UserTransactionsListView.as_view(), name='user_transactions'),
    path('statistics/saleTransactions/', UserSaleTransactionsListView.as_view(), name='user_sale_tran'),
    path('statistics/transactions/<int:pk>/', UserTransactionDetailView.as_view(), name='user_transaction_detail'),
    path('statistics/organizations/', UserTransactionOrganizationView.as_view(), name='transaction_organizations'),
    path('statistics/saleOrganizations/', UserSaleTransactionOrganizationView.as_view(),
         name='sale_transaction_organizations'),
    path('statistics/unprocessedTranCount/', UserUnprocessedTransactionCountView.as_view(),
         name='unprocessed_transaction_count'),
    path('statistics/<int:pk>/partners_totals/', PartnersTotalStatsView.as_view(), name='partners_totals'),
    path('statistics/<int:pk>/totals/', OrganizationTotalsView.as_view(), name='organization_totals'),
    path('orgTransactions/calendar/', OrganizationTransactionCalendarView.as_view(), name='org_client_calendar'),
]
