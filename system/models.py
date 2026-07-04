from django.db import models


class SiteSettings(models.Model):
    """站点级别的设置（单例模型）。"""
    admin_enabled = models.BooleanField('管理平台启用', default=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return f"SiteSettings(admin_enabled={self.admin_enabled})"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = '站点设置'
        verbose_name_plural = '站点设置'
