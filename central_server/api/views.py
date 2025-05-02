from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from oauth2_provider.models import Application
from .serializers import (
    SmartMeterCredentialSerializer,
    SmartMeterSerializer,
    SmartMeterEnodeUploadSerializer,
    BCOrderSerializer,
    BCTransactionSerializer,
)
from .models import SmartMeter, ClusterRegistration, BCOrder, BCTransaction
from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasScope
from django.utils import timezone
import secrets
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import models
from datetime import datetime, timedelta
from pytz import UTC
from django.db.models import Count, Sum, Q, Avg
from django.db.models.functions import TruncDate
from .serializers import (
    AnalyticsSummarySerializer,
    TimeSeriesPointSerializer,
)


# Your existing helper—filters by optional smart_meter_id query param
def _filter_by_meters(request):
    meter_ids = request.query_params.get("smart_meter_id")
    if meter_ids:
        ids = [u.strip() for u in meter_ids.split(",") if u.strip()]
        order_qs = BCOrder.objects.filter(smart_meter__uuid__in=ids)
        tx_qs = BCTransaction.objects.filter(order__smart_meter__uuid__in=ids)
    else:
        order_qs = BCOrder.objects.all()
        tx_qs = BCTransaction.objects.all()
    return order_qs, tx_qs


class AnalyticsSummaryAPIView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ["openid"]

    def get(self, request):
        order_qs, tx_qs = _filter_by_meters(request)

        # use explicit aliases for each filtered Sum()
        agg = tx_qs.aggregate(
            total_energy_bought=Sum("amount", filter=Q(transaction_type="buy")),
            total_energy_sold=Sum("amount", filter=Q(transaction_type="sell")),
        )

        summary = {
            "total_orders": order_qs.count(),
            "total_transactions": tx_qs.count(),
            "total_energy_bought": agg["total_energy_bought"] or 0,
            "total_energy_sold": agg["total_energy_sold"] or 0,
        }
        serializer = AnalyticsSummarySerializer(summary)
        return Response(serializer.data)


class TransactionsOverTimeAPIView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ["openid"]

    def get(self, request):
        _, tx_qs = _filter_by_meters(request)
        data = (
            tx_qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("uuid"), total_amount=Sum("amount"))
            .order_by("date")
        )
        serializer = TimeSeriesPointSerializer(data, many=True)
        return Response(serializer.data)


class EnergyFlowAPIView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ["openid"]

    def get(self, request):
        _, tx_qs = _filter_by_meters(request)
        data = (
            tx_qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                energy_bought=Sum("amount", filter=Q(transaction_type="buy")),
                energy_sold=Sum("amount", filter=Q(transaction_type="sell")),
            )
            .order_by("date")
        )
        serializer = TimeSeriesPointSerializer(data, many=True)
        return Response(serializer.data)


class AvgPriceOverTimeAPIView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ["openid"]

    def get(self, request):
        _, tx_qs = _filter_by_meters(request)
        data = (
            tx_qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(avg_price=Avg("executed_price"))
            .order_by("date")
        )
        serializer = TimeSeriesPointSerializer(data, many=True)
        return Response(serializer.data)


class BCOrderAPIView(APIView):
    """
    POST: Create a new BCOrder.
    PUT: Update fields on an existing BCOrder (price, state, total_amount).
    """

    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasScope]
    required_scopes = ["smart_meter"]

    def get(self, _):
        orders = BCOrder.objects.all()
        serializer = BCOrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BCOrderSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            order = serializer.save()
            return Response(
                BCOrderSerializer(order).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        order_id = request.data.get("order_id")
        try:
            order = BCOrder.objects.get(order_id=order_id)
        except BCOrder.DoesNotExist:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = BCOrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BCTransactionAPIView(APIView):
    """
    POST: Create a new BCTransaction and update the parent BCOrder's filled_amount and
    state.
    """

    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasScope]
    required_scopes = ["smart_meter"]

    def get(self, _):
        txs = BCTransaction.objects.all().select_related("order")
        serializer = BCTransactionSerializer(txs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BCTransactionSerializer(data=request.data)
        if serializer.is_valid():
            tx = serializer.save()
            return Response(
                BCTransactionSerializer(tx).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Custom pagination class using 'page' and 'limit' query parameters
class GeneralPagination(PageNumberPagination):
    page_size = 100
    page_query_param = "page"
    page_size_query_param = "limit"
    max_page_size = 100


class SmartMeterListAPIView(generics.ListAPIView):
    queryset = (
        SmartMeter.objects.all()
        .order_by(models.F("last_ping_ts").desc(nulls_last=True))
        .annotate(total_orders=models.Count("orders", distinct=True))
    )
    serializer_class = SmartMeterSerializer
    pagination_class = GeneralPagination

    # Require OAuth2 authentication with the 'openid' scope.
    authentication_classes = [OAuth2Authentication]
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ["openid"]


class SmartMeterEnodeApiView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasScope]
    required_scopes = ["smart_meter"]

    def get(self, _: Request):
        time_lower_bound = datetime.now(UTC) - timedelta(seconds=60)
        enodes = list(
            SmartMeter.objects.filter(
                enode__isnull=False, last_ping_ts__gte=time_lower_bound
            ).values_list("enode", flat=True)
        )
        return Response({"enodes": enodes}, status=status.HTTP_200_OK)

    def post(self, request: Request):
        serializer = SmartMeterEnodeUploadSerializer(data=request.data)
        if serializer.is_valid():
            smart_meter, _ = SmartMeter.objects.get_or_create(
                application=request.auth.application
            )
            smart_meter.enode = serializer.validated_data.get("enode")
            smart_meter.save(update_fields=["enode"])

            return Response(
                {"message": "Enode uploaded successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SmartMeterPingView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasScope]
    required_scopes = ["smart_meter"]

    def post(self, request):
        current_time = timezone.now()
        smart_meter = SmartMeter.objects.filter(
            application=request.auth.application
        ).first()

        if smart_meter:
            smart_meter.last_ping_ts = current_time
            smart_meter.save(update_fields=["last_ping_ts"])

            # Send a message to the "meter_status" group.
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "meter_status",
                {
                    "type": "meter_status",
                    "data": {
                        "timestamp": current_time.isoformat(),
                        "smart_meter_id": str(smart_meter.uuid),
                        "last_ping_ts": smart_meter.last_ping_ts.isoformat(),
                        "total_orders": (
                            BCOrder.objects.filter(smart_meter=smart_meter).count()
                        ),
                    },
                },
            )

        return Response(status=status.HTTP_200_OK)


class ClusterRegistrationView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        token = request.data.get("registration_token")
        if not token:
            return Response(
                {"error": "registration_token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            registration = ClusterRegistration.objects.get(token=token)
        except ClusterRegistration.DoesNotExist:
            return Response(
                {"error": "Invalid registration token"},
                status=status.HTTP_404_NOT_FOUND,
            )

        smart_meters = registration.smart_meters.all()

        # If smart meters already exist, return them
        if smart_meters.exists():
            registration.used_count += 1
            registration.last_used = timezone.now()
            registration.save(update_fields=["used_count", "last_used"])
            serializer = SmartMeterCredentialSerializer(smart_meters, many=True)
            return Response(
                {
                    "registration": str(registration.token),
                    "count": smart_meters.count(),
                    "clients": serializer.data,
                }
            )

        # Otherwise, create new applications and SmartMeters
        new_smart_meters = []
        for _ in range(registration.quantity):
            raw_client_secret = secrets.token_urlsafe(32)
            app = Application.objects.create(
                name=f"SmartMeter - {registration.uuid}",
                client_type=Application.CLIENT_CONFIDENTIAL,
                client_secret=raw_client_secret,
                authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            )
            sm = SmartMeter.objects.create(
                registration=registration,
                application=app,
                raw_client_secret=raw_client_secret,
            )
            new_smart_meters.append(sm)

        registration.used_count = 1
        registration.last_used = timezone.now()
        registration.save(update_fields=["used_count", "last_used"])

        serializer = SmartMeterCredentialSerializer(new_smart_meters, many=True)
        return Response(
            {
                "registration": str(registration.token),
                "count": len(new_smart_meters),
                "clients": serializer.data,
            }
        )
