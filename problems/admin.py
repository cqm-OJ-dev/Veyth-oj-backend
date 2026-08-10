from django.contrib import admin
from .models import Problem

# Register your models here.

class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'difficulty')
    list_filter = ('difficulty', 'created_at', 'updated_at')

admin.site.register(Problem, ProblemAdmin)