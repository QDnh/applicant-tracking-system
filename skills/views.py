from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import SkillForm
from .models import Skill


class SkillListView(ListView):
    model = Skill
    context_object_name = "skills"


class SkillCreateView(SuccessMessageMixin, CreateView):
    model = Skill
    form_class = SkillForm
    success_url = reverse_lazy("skills:list")
    success_message = 'Skill "%(name)s" added.'


class SkillUpdateView(SuccessMessageMixin, UpdateView):
    model = Skill
    form_class = SkillForm
    success_url = reverse_lazy("skills:list")
    success_message = 'Skill renamed to "%(name)s".'


class SkillDeleteView(DeleteView):
    model = Skill
    success_url = reverse_lazy("skills:list")

    def dispatch(self, request, *args, **kwargs):
        # Refuse both the confirm page (GET) and the delete itself (POST) while in use.
        skill = self.get_object()
        job_count = skill.job_openings.count()
        if job_count:
            uses = "job opening uses" if job_count == 1 else "job openings use"
            messages.error(
                request,
                f'Skill "{skill}" can\'t be deleted because {job_count} {uses} it. '
                "Remove it from those jobs first.",
            )
            return redirect("skills:list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Skill "{self.object}" deleted.')
        return response
