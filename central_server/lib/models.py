from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    created_at = models.DateTimeField(null=False, default=timezone.now, editable=False)
    updated_at = models.DateTimeField(null=False, default=timezone.now, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()

        return super().save(*args, **kwargs)
