# api/urls.py
from .views import (
    ClusterRegistrationView,
    SmartMeterPingView,
    SmartMeterListAPIView,
    SmartMeterEnodeApiView,
    BCOrderAPIView,
    BCTransactionAPIView,
    AnalyticsSummaryAPIView,
    TransactionsOverTimeAPIView,
    EnergyFlowAPIView,
    AvgPriceOverTimeAPIView,
)
from django.urls import path, include

analytics_patterns = [
    path("summary/", AnalyticsSummaryAPIView.as_view(), name="analytics-summary"),
    path(
        "transactions_over_time/",
        TransactionsOverTimeAPIView.as_view(),
        name="analytics-tx-time",
    ),
    path("energy_flow/", EnergyFlowAPIView.as_view(), name="analytics-energy-flow"),
    path(
        "avg_price_over_time/",
        AvgPriceOverTimeAPIView.as_view(),
        name="analytics-avg-price",
    ),
]


urlpatterns = [
    path("analytics/", include((analytics_patterns, "analytics"))),
    path("meters/", SmartMeterListAPIView.as_view(), name="smart_meter_list"),
    path("register/", ClusterRegistrationView.as_view(), name="cluster_registration"),
    path("ping/", SmartMeterPingView.as_view(), name="smart_meter_ping"),
    path("enodes/", SmartMeterEnodeApiView.as_view(), name="smart_meter_enodes"),
    path("orders/", BCOrderAPIView.as_view(), name="order_view"),
    path("transactions/", BCTransactionAPIView.as_view(), name="bc_transaction_view"),
]
