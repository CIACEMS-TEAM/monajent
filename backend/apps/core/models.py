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

class AuthEventLog(models.Model):
    event = models.CharField(max_length=64)
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='auth_events')
    phone_hash = models.CharField(max_length=128, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    success = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['phone_hash']),
        ]

    def __str__(self) -> str:
        return f"AuthEvent<{self.event}:{'OK' if self.success else 'KO'}>"
