from django import forms

from candidates.models import Candidate
from jobs.models import JobOpening

from .models import Application

SELECT = "select select-bordered w-full"


class RecordApplicationFromJobForm(forms.Form):
    """On a job page: pick the candidate who applied."""

    candidate = forms.ModelChoiceField(
        queryset=Candidate.objects.none(),
        empty_label="Choose a candidate…",
        widget=forms.Select(attrs={"class": SELECT}),
    )

    def __init__(self, *args, job, **kwargs):
        super().__init__(*args, **kwargs)
        self.job = job
        self.fields["candidate"].queryset = Application.eligible_candidates(job)


class RecordApplicationFromCandidateForm(forms.Form):
    """On a candidate page: pick the job they applied to."""

    job_opening = forms.ModelChoiceField(
        queryset=JobOpening.objects.none(),
        label="Job opening",
        empty_label="Choose a job opening…",
        widget=forms.Select(attrs={"class": SELECT}),
    )

    def __init__(self, *args, candidate, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidate = candidate
        self.fields["job_opening"].queryset = Application.eligible_jobs(candidate)
