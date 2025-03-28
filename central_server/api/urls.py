# api/urls.py
from django.urls import path
from .views import (
    ClusterRegistrationView,
    BatchTransactionUploadView,
    TransactionListAPIView,
    SmartMeterPingView,
)

urlpatterns = [
    path(
        "transactions/batch_upload/",
        BatchTransactionUploadView.as_view(),
        name="batch-transaction-upload",
    ),
    path("transactions/", TransactionListAPIView.as_view(), name="transaction_list"),
    path("register/", ClusterRegistrationView.as_view(), name="cluster_registration"),
    path("ping/", SmartMeterPingView.as_view(), name="smart_meter_ping"),
]
