from django.urls import path

from .views import TransactionCompleteView, TransactionPreprocessView

urlpatterns = [
    path('transactions/preprocess/', TransactionPreprocessView.as_view(), name='transaction_preprocess'),
    path('transactions/complete/', TransactionCompleteView.as_view(), name='transaction_complete'),
]
