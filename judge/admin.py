from django.contrib import admin
from .models import Submission, JudgeResult

class JudgeResultInline(admin.TabularInline):
    model = JudgeResult
    extra = 0
    readonly_fields = ('case_index', 'status', 'time_ms', 'wall_time_ms', 'memory_kb', 'returncode', 'stdout', 'stderr')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'problem', 'language', 'status', 'passed_cases', 'total_cases', 'max_time_ms', 'created_at')
    list_filter = ('language', 'status', 'created_at')
    search_fields = ('user__username', 'problem__title')
    inlines = [JudgeResultInline]
    readonly_fields = ('status', 'passed_cases', 'total_cases', 'max_time_ms', 'max_memory_mb', 'error_message', 'created_at')

admin.site.register(Submission, SubmissionAdmin)
