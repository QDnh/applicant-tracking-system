from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import JobOpeningForm
from .models import JobOpening


def job_list(request):
    status = request.GET.get("status")
    if status not in JobOpening.Status.values:
        status = JobOpening.Status.OPEN
    q = request.GET.get("q", "").strip()

    jobs = JobOpening.objects.filter(status=status)
    if q:
        jobs = jobs.filter(title__icontains=q)

    return render(
        request,
        "jobs/job_list.html",
        {"jobs": jobs, "status": status, "q": q, "statuses": JobOpening.Status.choices},
    )


def job_detail(request, pk):
    job = get_object_or_404(JobOpening.objects.prefetch_related("skills"), pk=pk)
    return render(request, "jobs/job_detail.html", {"job": job})


def job_create(request):
    form = JobOpeningForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save()
        messages.success(request, f'Job opening "{job}" created.')
        return redirect("jobs:detail", pk=job.pk)
    return render(request, "jobs/job_form.html", {"form": form})


def job_update(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    form = JobOpeningForm(request.POST or None, instance=job)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Job opening "{job}" updated.')
        return redirect("jobs:detail", pk=job.pk)
    return render(request, "jobs/job_form.html", {"form": form, "job": job})


def job_delete(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    if request.method == "POST":
        job.delete()
        messages.success(request, f'Job opening "{job}" deleted.')
        return redirect("jobs:list")
    return render(request, "jobs/job_confirm_delete.html", {"job": job})


@require_POST
def job_toggle_status(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    job.status = JobOpening.Status.CLOSED if job.is_open else JobOpening.Status.OPEN
    job.save(update_fields=["status", "updated_at"])
    messages.success(request, f'Job opening "{job}" is now {job.get_status_display().lower()}.')
    return redirect("jobs:detail", pk=job.pk)
