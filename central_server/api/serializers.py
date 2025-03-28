# api/serializers.py
from rest_framework import serializers
from .models import Transaction
from .models import SmartMeter


class SmartMeterCredentialSerializer(serializers.ModelSerializer):
    client_id = serializers.CharField(source="application.client_id")
    client_secret = serializers.CharField(source="raw_client_secret")

    class Meta:
        model = SmartMeter
        fields = ["client_id", "client_secret"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class TransactionUploadSerializer(serializers.Serializer):
    energy_kwh = serializers.FloatField()
    transaction_type = serializers.ChoiceField(
        choices=[("production", "Production"), ("consumption", "Consumption")]
    )
    timestamp = serializers.DateTimeField()


class BatchTransactionUploadSerializer(serializers.Serializer):
    transactions = TransactionUploadSerializer(many=True)
