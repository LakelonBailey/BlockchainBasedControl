# api/urls.py
from django.urls import path
from .views import (
    SmartMeterRegistrationView,
    BatchTransactionUploadView,
    TransactionListAPIView,
)

urlpatterns = [
    path(
        "smartmeters/register/",
        SmartMeterRegistrationView.as_view(),
        name="smartmeter-register",
    ),
    path(
        "transactions/batch_upload/",
        BatchTransactionUploadView.as_view(),
        name="batch-transaction-upload",
    ),
    path("transactions/", TransactionListAPIView.as_view(), name="transaction_list"),
]
