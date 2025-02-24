# api/views.py
import uuid
import secrets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from oauth2_provider.models import Application
from .serializers import (
    SmartMeterRegistrationSerializer,
    BatchTransactionUploadSerializer,
)
from .models import SmartMeter, Transaction

# api/views.py
from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasScope


class BatchTransactionUploadView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasScope]
    required_scopes = ["transactions:upload"]

    def post(self, request, format=None):
        serializer = BatchTransactionUploadSerializer(data=request.data)
        smart_meter = SmartMeter.objects.get(application=request.auth.application)
        if serializer.is_valid():
            transactions = serializer.validated_data.get("transactions", [])
            transaction_objects = [
                Transaction(**transaction, smart_meter=smart_meter)
                for transaction in transactions
            ]
            Transaction.objects.bulk_create(transaction_objects)
            count = len(transactions)

            return Response(
                {"message": f"{count} transactions uploaded successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SmartMeterRegistrationView(APIView):
    # Allow unauthenticated requests for registration.
    authentication_classes = []
    permission_classes = []

    def post(self, request, format=None):
        serializer = SmartMeterRegistrationSerializer(data=request.data, context={})
        if serializer.is_valid():
            device_id = serializer.validated_data["device_id"]
            public_key = serializer.validated_data["public_key"]

            # Check if the device is already registered.
            try:
                meter = SmartMeter.objects.get(device_id=device_id)

                # Return the stored credentials (client_id from the Application and
                # plain_client_secret).
                return Response(
                    {
                        "client_id": meter.application.client_id,
                        "client_secret": meter.plain_client_secret,
                    },
                    status=status.HTTP_200_OK,
                )
            except SmartMeter.DoesNotExist:

                # The device is not registered yet.
                # Generate a plain text secret using the secrets module.
                client_id = uuid.uuid4().hex
                plain_client_secret = secrets.token_urlsafe(32)

                # Create a new OAuth2 Application using Client Credentials grant type.
                app = Application.objects.create(
                    name=f"SmartMeter-{device_id}",
                    client_id=client_id,
                    client_secret=plain_client_secret,
                    user=None,
                    client_type=Application.CLIENT_CONFIDENTIAL,
                    authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
                )

                # Mark the provisioning token as used.
                token_obj = serializer.context.get("token_obj")
                if token_obj:
                    token_obj.is_used = True
                    token_obj.device_id = device_id
                    token_obj.save()

                # Create a SmartMeter record and store the plain text client secret.
                SmartMeter.objects.create(
                    device_id=device_id,
                    public_key=public_key,
                    application=app,
                    plain_client_secret=plain_client_secret,
                )

                return Response(
                    {
                        "client_id": client_id,
                        "client_secret": plain_client_secret,
                    },
                    status=status.HTTP_201_CREATED,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
