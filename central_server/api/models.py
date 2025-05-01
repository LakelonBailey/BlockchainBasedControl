from django.db import models
from lib.models import BaseModel
import secrets


def generate_provisioning_token():
    return secrets.token_urlsafe(32)


class ClusterRegistration(BaseModel):
    token = models.CharField(
        default=generate_provisioning_token, unique=True, editable=False, max_length=50
    )
    quantity = models.PositiveIntegerField()
    used_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"Registration {self.token} ({self.quantity})"


class SmartMeter(BaseModel):
    registration = models.ForeignKey(
        ClusterRegistration,
        on_delete=models.CASCADE,
        related_name="smart_meters",
        null=True,
    )
    application = models.OneToOneField(
        "oauth2_provider.Application",
        on_delete=models.CASCADE,
        related_name="smart_meter",
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    raw_client_secret = models.CharField(max_length=100, null=True)
    last_ping_ts = models.DateTimeField(null=True)
    enode = models.CharField(max_length=1000, null=True)

    def __str__(self):
        return str(self.application.client_id)


class BCOrder(BaseModel):
    order_id = models.CharField(max_length=1000, unique=True, db_index=True)
    smart_meter = models.ForeignKey(
        SmartMeter, on_delete=models.CASCADE, null=True, related_name="orders"
    )
    order_type = models.CharField(
        max_length=4,
        choices=(
            ("buy", "Buy"),
            ("sell", "Sell"),
        ),
        null=False,
    )
    state = models.CharField(
        max_length=10,
        choices=(
            ("placed", "Placed"),
            ("matched", "Matched"),
            ("cancelled", "Cancelled"),
        ),
        null=False,
        default="placed",
    )
    total_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    filled_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    is_partial = models.BooleanField(default=True)


class BCTransaction(BaseModel):
    order = models.ForeignKey(
        BCOrder,
        on_delete=models.CASCADE,
        related_name="transactions",
        null=False,
    )
    executed_price = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    transaction_type = models.CharField(
        max_length=4,
        choices=(
            ("buy", "Buy"),
            ("sell", "Sell"),
        ),
        null=False,
    )
