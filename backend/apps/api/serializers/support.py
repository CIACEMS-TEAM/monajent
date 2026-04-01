"""
Serializers Support — Monajent
──────────────────────────────
• SupportMessageSerializer   → message dans un ticket
• SupportTicketListSerializer → liste compacte des tickets
• SupportTicketDetailSerializer → ticket + messages
• SupportTicketCreateSerializer → création ticket + premier message
• SupportMessageCreateSerializer → ajout message à un ticket
"""

from rest_framework import serializers

from apps.support.models import SupportTicket, SupportMessage


class SupportMessageSerializer(serializers.ModelSerializer):
    author_phone = serializers.CharField(source='author.phone', default='', read_only=True)
    author_name = serializers.CharField(source='author.username', default='', read_only=True)

    class Meta:
        model = SupportMessage
        fields = [
            'id', 'author_phone', 'author_name',
            'content', 'is_staff_reply', 'created_at',
        ]
        read_only_fields = fields


class SupportTicketListSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    priority_label = serializers.CharField(source='get_priority_display', read_only=True)
    messages_count = serializers.SerializerMethodField()
    last_reply_at = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'subject', 'category', 'category_label',
            'status', 'status_label', 'priority', 'priority_label',
            'messages_count', 'last_reply_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_messages_count(self, obj) -> int:
        return obj.messages.count()

    def get_last_reply_at(self, obj):
        last = obj.messages.order_by('-created_at').first()
        return last.created_at if last else None


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    priority_label = serializers.CharField(source='get_priority_display', read_only=True)
    messages = SupportMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'subject', 'category', 'category_label',
            'status', 'status_label', 'priority', 'priority_label',
            'messages',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class SupportTicketCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    category = serializers.ChoiceField(choices=SupportTicket.Category.choices)
    content = serializers.CharField()

    def create(self, validated_data):
        user = self.context['request'].user
        ticket = SupportTicket.objects.create(
            user=user,
            subject=validated_data['subject'],
            category=validated_data['category'],
        )
        SupportMessage.objects.create(
            ticket=ticket,
            author=user,
            content=validated_data['content'],
            is_staff_reply=False,
        )
        return ticket


class SupportMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
