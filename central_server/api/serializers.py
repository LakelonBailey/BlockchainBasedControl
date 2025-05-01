# api/serializers.py
from rest_framework import serializers
from .models import Transaction, SmartMeter, BCOrder, BCTransaction
from django.db.models import Sum
from django.db import transaction


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
            "created_at",
        ]
        read_only_fields = ["transaction_type", "created_at"]

    def create(self, validated_data):
        order_id = validated_data.pop("order_id")
        order = BCOrder.objects.get(order_id=order_id)
        # Infer the opposite transaction type
        transaction_type = "buy" if order.order_type == "sell" else "sell"
        amount = validated_data["amount"]

        with transaction.atomic():
            tx = BCTransaction.objects.create(
                order=order,
                amount=amount,
                transaction_type=transaction_type,
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


class SmartMeterAnalysisSerializer(serializers.ModelSerializer):
    total_transactions = serializers.SerializerMethodField()
    avg_transactions_per_day = serializers.SerializerMethodField()
    avg_net_kwh_per_day = serializers.SerializerMethodField()

    class Meta:
        model = SmartMeter
        # We include only the fields we want; raw_client_secret and application are
        # omitted.
        fields = (
            "id",
            "registration",
            "registered_at",
            "last_ping_ts",
            "total_transactions",
            "avg_transactions_per_day",
            "avg_net_kwh_per_day",
        )

    def get_total_transactions(self, obj):
        return obj.transactions.count()

    def get_avg_transactions_per_day(self, obj):
        qs = obj.transactions.exclude(timestamp__isnull=True).order_by("timestamp")
        if not qs.exists():
            return 0
        # Use the first and last transaction dates to determine the span (inclusive)
        first_date = qs.first().timestamp.date()
        last_date = qs.last().timestamp.date()
        days = (last_date - first_date).days + 1  # ensure at least one day
        return qs.count() / days if days > 0 else qs.count()

    def get_avg_net_kwh_per_day(self, obj):
        qs = obj.transactions.exclude(timestamp__isnull=True).order_by("timestamp")
        if not qs.exists():
            return 0
        # Calculate net kWh: add production, subtract consumption
        production = (
            qs.filter(transaction_type="production").aggregate(total=Sum("energy_kwh"))[
                "total"
            ]
            or 0
        )
        consumption = (
            qs.filter(transaction_type="consumption").aggregate(
                total=Sum("energy_kwh")
            )["total"]
            or 0
        )
        net = production - consumption
        first_date = qs.first().timestamp.date()
        last_date = qs.last().timestamp.date()
        days = (last_date - first_date).days + 1
        return net / days if days > 0 else net


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


class SmartMeterSerializer(serializers.ModelSerializer):
    total_transactions = serializers.IntegerField()

    class Meta:
        model = SmartMeter
        fields = ["uuid", "registered_at", "last_ping_ts", "total_transactions"]


class TransactionUploadSerializer(serializers.Serializer):
    energy_kwh = serializers.FloatField()
    transaction_type = serializers.ChoiceField(
        choices=[("production", "Production"), ("consumption", "Consumption")]
    )
    timestamp = serializers.DateTimeField()


class BatchTransactionUploadSerializer(serializers.Serializer):
    transactions = TransactionUploadSerializer(many=True)


class SmartMeterEnodeUploadSerializer(serializers.Serializer):
    enode = serializers.CharField()
