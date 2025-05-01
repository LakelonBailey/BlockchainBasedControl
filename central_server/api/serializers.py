# api/serializers.py
from rest_framework import serializers
from .models import SmartMeter, BCOrder, BCTransaction
from django.db import transaction


class AnalyticsSummarySerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    total_energy_bought = serializers.DecimalField(max_digits=20, decimal_places=8)
    total_energy_sold = serializers.DecimalField(max_digits=20, decimal_places=8)


class TimeSeriesPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField(required=False)
    total_amount = serializers.DecimalField(
        max_digits=20, decimal_places=8, required=False
    )
    energy_bought = serializers.DecimalField(
        max_digits=20, decimal_places=8, required=False
    )
    energy_sold = serializers.DecimalField(
        max_digits=20, decimal_places=8, required=False
    )
    avg_price = serializers.DecimalField(
        max_digits=20, decimal_places=8, required=False
    )


class BCOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = BCOrder
        fields = [
            "order_id",
            "order_type",
            "state",
            "total_amount",
            "filled_amount",
            "price",
            "is_partial",
            "created_at",
        ]
        read_only_fields = ["filled_amount", "created_at"]

    def create(self, validated_data):
        # Grab the current request from serializer context
        request = self.context.get("request")
        if not request or not hasattr(request, "auth") or not request.auth:
            raise serializers.ValidationError(
                "Authentication credentials were not provided."
            )

        # Find the SmartMeter tied to this OAuth2 application
        try:
            sm = SmartMeter.objects.get(application=request.auth.application)
        except SmartMeter.DoesNotExist:
            raise serializers.ValidationError(
                "No SmartMeter found for this client application."
            )

        # Inject it into the data we’ll save
        validated_data["smart_meter"] = sm
        return super().create(validated_data)


class BCTransactionSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(write_only=True)

    class Meta:
        model = BCTransaction
        fields = [
            "order_id",
            "amount",
            "transaction_type",
            "executed_price",
            "created_at",
        ]
        read_only_fields = ["transaction_type", "created_at"]

    def create(self, validated_data):
        order_id = validated_data.pop("order_id")
        order = BCOrder.objects.get(order_id=order_id)
        # Infer the opposite transaction type
        transaction_type = "buy" if order.order_type == "sell" else "sell"
        amount = validated_data["amount"]
        executed_price = validated_data["executed_price"]

        with transaction.atomic():
            tx = BCTransaction.objects.create(
                order=order,
                amount=amount,
                transaction_type=transaction_type,
                executed_price=executed_price,
            )
            # Update filled amount and order state
            order.filled_amount += amount
            if order.filled_amount >= order.total_amount:
                order.is_partial = False
                order.state = "matched"
            order.save()
        return tx

    def to_representation(self, instance):
        # Include the related order's order_id in the response
        data = super().to_representation(instance)
        data["order_id"] = instance.order.order_id
        return data


class SmartMeterCredentialSerializer(serializers.ModelSerializer):
    client_id = serializers.CharField(source="application.client_id")
    client_secret = serializers.CharField(source="raw_client_secret")

    class Meta:
        model = SmartMeter
        fields = ["client_id", "client_secret"]


class SmartMeterSerializer(serializers.ModelSerializer):
    total_orders = serializers.IntegerField()

    class Meta:
        model = SmartMeter
        fields = ["uuid", "registered_at", "last_ping_ts", "total_orders"]


class SmartMeterEnodeUploadSerializer(serializers.Serializer):
    enode = serializers.CharField()
