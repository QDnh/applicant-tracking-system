from django.db import models
from django.urls import reverse

from skills.models import Skill


class JobOpening(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    skills = models.ManyToManyField(Skill, blank=True, related_name="job_openings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("jobs:detail", args=[self.pk])

    @property
    def is_open(self):
        return self.status == self.Status.OPEN
