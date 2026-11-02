from django.contrib import admin

from .models import Application, StageChange


class StageChangeInline(admin.TabularInline):
    """Read-only: stage history is append-only."""

    model = StageChange
    extra = 0
    can_delete = False
    readonly_fields = ["from_stage", "to_stage", "changed_by", "changed_at"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Read-only: applications are recorded and moved through the app, never edited here."""

    list_display = ["candidate", "job_opening", "stage", "applied_at"]
    list_filter = ["stage"]
    search_fields = ["candidate__first_name", "candidate__last_name", "job_opening__title"]
    inlines = [StageChangeInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
