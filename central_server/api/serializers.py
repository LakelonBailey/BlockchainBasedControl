# api/serializers.py
from rest_framework import serializers
from .models import ProvisioningToken


class TransactionSerializer(serializers.Serializer):
    energy_kwh = serializers.FloatField()
    transaction_type = serializers.ChoiceField(
        choices=[("production", "Production"), ("consumption", "Consumption")]
    )


class BatchTransactionUploadSerializer(serializers.Serializer):
    transactions = TransactionSerializer(many=True)


class SmartMeterRegistrationSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=100)
    provisioning_token = serializers.CharField(max_length=100)
    public_key = serializers.CharField()

    def validate_provisioning_token(self, value):
        try:
            token_obj = ProvisioningToken.objects.get(token=value)
        except ProvisioningToken.DoesNotExist:
            raise serializers.ValidationError("Invalid provisioning token")

        # if token_obj.is_used:
        #     raise serializers.ValidationError("Provisioning token already used")

        # if token_obj.is_expired():
        #     raise serializers.ValidationError("Provisioning token expired")

        self.context["token_obj"] = token_obj
        return value
