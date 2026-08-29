from django.contrib import admin
from .models import Problem, Example, TestCase

class ExampleInline(admin.StackedInline):
    model = Example
    extra = 1
    ordering = ('order',)

class TestCaseInline(admin.StackedInline):
    model = TestCase
    extra = 1
    ordering = ('order',)

class ProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'difficulty', 'time_limit_ms', 'memory_limit_mb',
                    'accepted', 'submissions', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'difficulty')
    list_filter = ('difficulty', 'created_at', 'updated_at')
    inlines = [ExampleInline, TestCaseInline]

admin.site.register(Problem, ProblemAdmin)
