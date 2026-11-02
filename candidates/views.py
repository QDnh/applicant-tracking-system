from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from applications.forms import RecordApplicationFromCandidateForm
from applications.models import Application

from .forms import CandidateForm
from .models import Candidate


class CandidateListView(ListView):
    template_name = "candidates/candidate_list.html"
    context_object_name = "candidates"

    def get_queryset(self):
        self.q = self.request.GET.get("q", "").strip()
        # Archived candidates are hidden; the Archived tab arrives in Phase 10.
        candidates = Candidate.objects.exclude(status=Candidate.Status.ARCHIVED)
        if self.q:
            candidates = candidates.annotate(
                full_name_search=Concat("first_name", Value(" "), "last_name")
            ).filter(
                Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
                | Q(email__icontains=self.q)
                | Q(full_name_search__icontains=self.q)
            )
        return candidates

    def get_context_data(self, **kwargs):
        return super().get_context_data(q=self.q, **kwargs)


class CandidateDetailView(DetailView):
    model = Candidate
    template_name = "candidates/candidate_detail.html"
    context_object_name = "candidate"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **Application.candidate_page_sections(self.object),
            record_form=RecordApplicationFromCandidateForm(candidate=self.object),
            **kwargs,
        )


class CandidateFormMixin(SuccessMessageMixin):
    model = Candidate
    form_class = CandidateForm
    template_name = "candidates/candidate_form.html"
    context_object_name = "candidate"

    def get_success_url(self):
        return reverse("candidates:detail", args=[self.object.pk])


class CandidateCreateView(CandidateFormMixin, CreateView):
    success_message = "Candidate %(first_name)s %(last_name)s created."


class CandidateUpdateView(CandidateFormMixin, UpdateView):
    success_message = "Candidate %(first_name)s %(last_name)s updated."


class CandidateDeleteView(DeleteView):
    model = Candidate
    template_name = "candidates/candidate_confirm_delete.html"
    context_object_name = "candidate"
    success_url = reverse_lazy("candidates:list")

    def dispatch(self, request, *args, **kwargs):
        # Refuse both the confirm page (GET) and the delete itself (POST) once any
        # application exists; the PROTECT foreign key enforces the same at the database.
        candidate = self.get_object()
        if candidate.applications.exists():
            messages.error(
                request,
                f"Candidate {candidate} can't be deleted because they have applications. "
                "Archive them instead to hide the record while keeping its history.",
            )
            return redirect(candidate)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Candidate {self.object} deleted.")
        return response
