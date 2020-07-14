from django.urls import path

from .views import TransactionPreprocessView

urlpatterns = [
    path('transactions/preprocess/', TransactionPreprocessView.as_view(), name='transaction_preprocess'),
]
