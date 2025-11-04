from django.db import models


class SmsDeliveryLog(models.Model):
    message_id = models.CharField(max_length=128, blank=True)
    address = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['address']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        return f"DLR<{self.message_id}:{self.status}>"

from django.db import models

# Create your models here.
