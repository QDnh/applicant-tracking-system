from django.contrib import admin

from .models import JobOpening


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["title"]
    filter_horizontal = ["skills"]
