from django.contrib import admin

from .models import SupportTicket, SupportMessage


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 1
    fields = ('author', 'content', 'is_staff_reply', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subject', 'category', 'status', 'priority', 'created_at', 'updated_at')
    list_filter = ('category', 'status', 'priority')
    search_fields = ('user__phone', 'user__username', 'subject')
    ordering = ('-updated_at',)
    readonly_fields = ('user', 'category', 'subject', 'created_at', 'updated_at')
    inlines = [SupportMessageInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, SupportMessage) and not obj.pk:
                if obj.is_staff_reply:
                    obj.author = request.user
                obj.save()
                if obj.is_staff_reply:
                    from .tasks import send_ticket_reply_email
                    send_ticket_reply_email.delay(obj.id)
            else:
                obj.save()
        formset.save_m2m()


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'author', 'is_staff_reply', 'created_at')
    list_filter = ('is_staff_reply',)
    search_fields = ('ticket__subject', 'author__phone', 'content')
    ordering = ('-created_at',)
