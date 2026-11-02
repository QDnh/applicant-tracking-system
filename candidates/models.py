from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Candidate(models.Model):
    class Source(models.TextChoices):
        LINKEDIN = "linkedin", "LinkedIn"
        REFERRAL = "referral", "Referral"
        COMPANY_WEBSITE = "company_website", "Company Website"
        JOB_BOARD = "job_board", "Job Board"
        CAREER_FAIR = "career_fair", "Career Fair"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DEACTIVATED = "deactivated", "Deactivated"
        ARCHIVED = "archived", "Archived"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        # Stored lowercase so the unique constraint ignores case.
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("candidates:detail", args=[self.pk])

    def clean(self):
        # Runs for ModelForms (including the admin), so they can't archive past the rule.
        super().clean()
        self._check_can_enter(self.status)

    def change_status(self, status):
        """The single entry point for status changes from the app.

        Any status can change to any other, except that entering Archived requires
        zero active applications. Raises ValidationError when refused.
        """
        if status not in self.Status.values:
            raise ValidationError("Choose a valid status.")
        self._check_can_enter(status)
        self.status = status
        self.save(update_fields=["status", "updated_at"])

    def _check_can_enter(self, status):
        if status != self.Status.ARCHIVED or self.pk is None:
            return
        # Imported here: applications.models imports this module at load time.
        from applications.models import Application

        active_count = self.applications.filter(stage__in=Application.ACTIVE_STAGES).count()
        if active_count:
            noun, pronoun = ("application", "it") if active_count == 1 else ("applications", "them")
            raise ValidationError(
                f"Candidate {self} can't be archived while they have {active_count} "
                f"active {noun}. Reject or withdraw {pronoun} first."
            )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
