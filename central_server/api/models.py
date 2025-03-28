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

    def __str__(self):
        return str(self.application.client_id)


class Transaction(BaseModel):
    TRANSACTION_TYPES = (
        ("production", "Production"),
        ("consumption", "Consumption"),
    )
    # Link each transaction to a SmartMeter.
    smart_meter = models.ForeignKey(
        SmartMeter, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    energy_kwh = models.DecimalField(max_digits=10, decimal_places=8)
    timestamp = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.smart_meter.uuid} - {self.transaction_type} - \
{self.energy_kwh} kWh"
