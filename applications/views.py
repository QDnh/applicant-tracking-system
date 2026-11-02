from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import FormView

from candidates.models import Candidate
from jobs.models import JobOpening

from .forms import RecordApplicationFromCandidateForm, RecordApplicationFromJobForm
from .models import Application


class RecordApplicationView(FormView):
    """POST-only: the form is shown on the job or candidate page, and every outcome
    redirects back there with a message. Defining no get() makes GET return 405."""

    http_method_names = ["post"]

    def get_success_url(self):
        return self.return_url

    def form_invalid(self, form):
        for errors in form.errors.values():
            for error in errors:
                messages.error(self.request, error)
        return redirect(self.return_url)

    def record(self, candidate, job_opening):
        try:
            Application.record(candidate, job_opening, self.request.user)
        except ValidationError as error:
            for message in error.messages:
                messages.error(self.request, message)
        else:
            messages.success(self.request, f"Recorded {candidate}'s application for {job_opening}.")
        return redirect(self.return_url)


class RecordFromJobView(RecordApplicationView):
    form_class = RecordApplicationFromJobForm

    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(JobOpening, pk=kwargs["job_pk"])
        self.return_url = self.job.get_absolute_url()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "job": self.job}

    def form_valid(self, form):
        return self.record(form.cleaned_data["candidate"], self.job)


class RecordFromCandidateView(RecordApplicationView):
    form_class = RecordApplicationFromCandidateForm

    def dispatch(self, request, *args, **kwargs):
        self.candidate = get_object_or_404(Candidate, pk=kwargs["candidate_pk"])
        self.return_url = self.candidate.get_absolute_url()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "candidate": self.candidate}

    def form_valid(self, form):
        return self.record(self.candidate, form.cleaned_data["job_opening"])
