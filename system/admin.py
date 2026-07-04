from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('admin_enabled', 'updated_at')

    def has_add_permission(self, request):
        # 仅允许 superuser 修改/新增
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # 强制只显示单例
        qs = super().get_queryset(request)
        return qs
