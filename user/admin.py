from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    fieldsets = DefaultUserAdmin.fieldsets + (
        (_('OJ 信息'), {
            'fields': (
                'nickname',
                'avatar',
                'bio',
                'school',
                'organization',
                'country',
                'rating',
                'solved_count',
                'submission_count',
                'accepted_count',
                'score',
                'last_submission_at',
                'is_banned',
            ),
        }),
    )
    list_display = (
        'username',
        'email',
        'nickname',
        'rating',
        'solved_count',
        'submission_count',
        'accepted_count',
        'is_banned',
        'is_staff',
    )
    search_fields = ('username', 'email', 'nickname')
