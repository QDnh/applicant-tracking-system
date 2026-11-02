from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from .forms import JobOpeningForm
from .models import JobOpening


class JobListView(ListView):
    template_name = "jobs/job_list.html"
    context_object_name = "jobs"

    def get_queryset(self):
        status = self.request.GET.get("status")
        if status not in JobOpening.Status.values:
            status = JobOpening.Status.OPEN
        self.status = status
        self.q = self.request.GET.get("q", "").strip()

        jobs = JobOpening.objects.filter(status=status)
        if self.q:
            jobs = jobs.filter(title__icontains=self.q)
        return jobs

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            status=self.status, q=self.q, statuses=JobOpening.Status.choices, **kwargs
        )


class JobDetailView(DetailView):
    queryset = JobOpening.objects.prefetch_related("skills")
    template_name = "jobs/job_detail.html"
    context_object_name = "job"


class JobFormMixin(SuccessMessageMixin):
    model = JobOpening
    form_class = JobOpeningForm
    template_name = "jobs/job_form.html"
    context_object_name = "job"

    def get_success_url(self):
        return reverse("jobs:detail", args=[self.object.pk])


class JobCreateView(JobFormMixin, CreateView):
    success_message = 'Job opening "%(title)s" created.'


class JobUpdateView(JobFormMixin, UpdateView):
    success_message = 'Job opening "%(title)s" updated.'


class JobDeleteView(DeleteView):
    model = JobOpening
    template_name = "jobs/job_confirm_delete.html"
    context_object_name = "job"
    success_url = reverse_lazy("jobs:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Job opening "{self.object}" deleted.')
        return response


class JobToggleStatusView(SingleObjectMixin, View):
    """POST-only: defining no get() makes GET return 405."""

    model = JobOpening

    def post(self, request, *args, **kwargs):
        job = self.get_object()
        job.status = JobOpening.Status.CLOSED if job.is_open else JobOpening.Status.OPEN
        job.save(update_fields=["status", "updated_at"])
        messages.success(request, f'Job opening "{job}" is now {job.get_status_display().lower()}.')
        return redirect("jobs:detail", pk=job.pk)
