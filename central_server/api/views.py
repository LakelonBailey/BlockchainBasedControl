from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from oauth2_provider.models import Application
from .serializers import (
    BatchTransactionUploadSerializer,
    TransactionSerializer,
    SmartMeterCredentialSerializer,
)
from .models import SmartMeter, Transaction, ClusterRegistration
from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasScope
from django.utils import timezone
import secrets


# Custom pagination class using 'page' and 'limit' query parameters
class TransactionPagination(PageNumberPagination):
    page_size = 10  # default items per page
    page_query_param = "page"  # for the current page number (default)
    page_size_query_param = "limit"  # allows client to set page size using "limit"
    max_page_size = 100


class TransactionListAPIView(generics.ListAPIView):
    queryset = Transaction.objects.all().order_by("-timestamp")
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination

    # Require OAuth2 authentication with the 'openid' scope.
    authentication_classes = [OAuth2Authentication]
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ["openid"]


class SmartMeterPingView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasScope]
    required_scopes = ["transactions:upload"]

    def post(self, request: Request):
        current_time = timezone.now()
        SmartMeter.objects.filter(application=request.auth.application).update(
            last_ping_ts=current_time
        )
        return Response(status=status.HTTP_200_OK)


class BatchTransactionUploadView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasScope]
    required_scopes = ["transactions:upload"]

    def post(self, request: Request):
        serializer = BatchTransactionUploadSerializer(data=request.data)
        smart_meter = SmartMeter.objects.get(application=request.auth.application)
        smart_meter.last_ping_ts = timezone.now()
        smart_meter.save(update_fields=["last_ping_ts"])
        if serializer.is_valid():
            transactions = serializer.validated_data.get("transactions", [])
            transaction_objects = [
                Transaction(
                    **transaction,
                    smart_meter=smart_meter,
                )
                for transaction in transactions
            ]
            Transaction.objects.bulk_create(transaction_objects)
            count = len(transactions)

            return Response(
                {"message": f"{count} transactions uploaded successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
