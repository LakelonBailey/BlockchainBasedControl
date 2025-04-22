# api/urls.py
from django.urls import path
from .views import (
    ClusterRegistrationView,
    BatchTransactionUploadView,
    TransactionListAPIView,
    SmartMeterPingView,
    SmartMeterListAPIView,
    SmartMeterDetailView,
    SmartMeterEnodeApiView,
)

urlpatterns = [
    path(
        "transactions/batch_upload/",
        BatchTransactionUploadView.as_view(),
        name="batch-transaction-upload",
    ),
    path("transactions/", TransactionListAPIView.as_view(), name="transaction_list"),
    path("meters/", SmartMeterListAPIView.as_view(), name="smart_meter_list"),
    path(
        "meters/<int:smart_meter_id>/analysis/",
        SmartMeterDetailView.as_view(),
        name="smart-meter-analysis",
    ),
    path("register/", ClusterRegistrationView.as_view(), name="cluster_registration"),
    path("ping/", SmartMeterPingView.as_view(), name="smart_meter_ping"),
    path("enodes/", SmartMeterEnodeApiView.as_view(), name="smart_meter_enodes"),
]
