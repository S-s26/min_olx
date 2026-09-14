from django.contrib import admin
from .models import UserActivity


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'title', 'created_at')
    list_filter = ('event',)
    search_fields = ('user__username', 'title', 'detail')
    readonly_fields = ('created_at',)