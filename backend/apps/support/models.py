from django.db import models


class SupportTicket(models.Model):
    class Category(models.TextChoices):
        BUG = 'BUG', 'Signalement de bug'
        SUGGESTION = 'SUGGESTION', 'Suggestion'
        COMPLAINT = 'COMPLAINT', 'Plainte'
        HELP = 'HELP', "Demande d'aide"
        OTHER = 'OTHER', 'Autre'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Ouvert'
        IN_PROGRESS = 'IN_PROGRESS', 'En cours'
        RESOLVED = 'RESOLVED', 'Résolu'
        CLOSED = 'CLOSED', 'Fermé'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Basse'
        NORMAL = 'NORMAL', 'Normale'
        HIGH = 'HIGH', 'Haute'

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='support_tickets',
    )
    category = models.CharField(max_length=16, choices=Category.choices)
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=8, choices=Priority.choices, default=Priority.NORMAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self) -> str:
        return f"Ticket#{self.pk} [{self.category}] {self.subject[:40]}"


class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name='messages',
    )
    author = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='support_messages',
    )
    content = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        sender = 'Staff' if self.is_staff_reply else 'User'
        return f"Msg#{self.pk} ({sender}) ticket={self.ticket_id}"
