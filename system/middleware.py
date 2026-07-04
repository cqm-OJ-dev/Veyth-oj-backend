from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class AdminEnabledMiddleware(MiddlewareMixin):
    """拦截 /admin/ 路径，当管理后台被禁用时返回提示。

    若管理员禁用（admin_enabled=False），普通用户访问 /admin/ 会收到 403 与提示。
    已认证的 superuser 可以绕过此限制以便修复设置。
    """

    def process_request(self, request):
        path = request.path
        if not path.startswith('/admin'):
            return None

        # 放行登录/登出页面，避免管理后台禁用时把 superuser 登录入口也拦住
        if path.startswith('/admin/login') or path.startswith('/admin/logout'):
            return None

        # 延迟导入以避免启动时依赖数据库不可用的问题
        try:
            from system.models import SiteSettings
            settings = SiteSettings.get_solo()
            enabled = bool(settings.admin_enabled)
        except Exception:
            enabled = True  # 如果无法读取 DB（例如迁移阶段），默认允许访问以避免锁死

        # 如果被禁用且非 superuser，则返回提示
        user = getattr(request, 'user', None)
        if not enabled and not (hasattr(user, 'is_superuser') and user.is_superuser):
            return HttpResponse('管理平台已禁用', status=403)

        return None
