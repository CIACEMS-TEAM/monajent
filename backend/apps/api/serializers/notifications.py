from rest_framework import serializers
from apps.users.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'category', 'title', 'message', 'is_read', 'created_at']
        read_only_fields = fields
