from django.contrib import admin

from .models import Candidate


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "email", "source", "status", "created_at"]
    list_filter = ["status", "source"]
    search_fields = ["first_name", "last_name", "email"]
