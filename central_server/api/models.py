from django.db import models
from django.utils import timezone
from lib.models import BaseModel
import secrets


def generate_provisioning_token():
    return secrets.token_urlsafe(32)


class ProvisioningToken(BaseModel):
    token = models.CharField(
        max_length=100, unique=True, default=generate_provisioning_token, editable=False
    )
    is_used = models.BooleanField(default=False)
    device_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def __str__(self):
        return self.token


class SmartMeter(BaseModel):
    device_id = models.CharField(max_length=100, unique=True)
    public_key = models.TextField()
    application = models.OneToOneField(
        "oauth2_provider.Application",
        on_delete=models.CASCADE,
        related_name="smart_meter",
    )
    plain_client_secret = models.CharField(
        max_length=256, blank=True, null=True
    )  # Store plain secret for re-registration
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.device_id


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
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.smart_meter.device_id} - {self.transaction_type} - \
{self.energy_kwh} kWh"
