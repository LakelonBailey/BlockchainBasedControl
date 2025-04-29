# api/urls.py
from django.urls import path
from .views import (
    ClusterRegistrationView,
    BatchTransactionUploadView,
    SmartMeterPingView,
    SmartMeterListAPIView,
    SmartMeterDetailView,
    SmartMeterEnodeApiView,
    BCOrderAPIView,
    BCTransactionAPIView,
)

urlpatterns = [
    path(
        "transactions/batch_upload/",
        BatchTransactionUploadView.as_view(),
        name="batch-transaction-upload",
    ),
    path("meters/", SmartMeterListAPIView.as_view(), name="smart_meter_list"),
    path(
        "meters/<int:smart_meter_id>/analysis/",
        SmartMeterDetailView.as_view(),
        name="smart-meter-analysis",
    ),
    path("register/", ClusterRegistrationView.as_view(), name="cluster_registration"),
    path("ping/", SmartMeterPingView.as_view(), name="smart_meter_ping"),
    path("enodes/", SmartMeterEnodeApiView.as_view(), name="smart_meter_enodes"),
    path("orders/", BCOrderAPIView.as_view(), name="order_view"),
    path("transactions/", BCTransactionAPIView.as_view(), name="bc_transaction_view"),
]
