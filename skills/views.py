from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SkillForm
from .models import Skill


def skill_list(request):
    return render(request, "skills/skill_list.html", {"skills": Skill.objects.all()})


def skill_create(request):
    form = SkillForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        skill = form.save()
        messages.success(request, f'Skill "{skill}" added.')
        return redirect("skills:list")
    return render(request, "skills/skill_form.html", {"form": form})


def skill_update(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    form = SkillForm(request.POST or None, instance=skill)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Skill renamed to "{skill}".')
        return redirect("skills:list")
    return render(request, "skills/skill_form.html", {"form": form, "skill": skill})


def skill_delete(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    job_count = skill.job_openings.count()
    if job_count:
        uses = "job opening uses" if job_count == 1 else "job openings use"
        messages.error(
            request,
            f'Skill "{skill}" can\'t be deleted because {job_count} {uses} it. '
            "Remove it from those jobs first.",
        )
        return redirect("skills:list")
    if request.method == "POST":
        skill.delete()
        messages.success(request, f'Skill "{skill}" deleted.')
        return redirect("skills:list")
    return render(request, "skills/skill_confirm_delete.html", {"skill": skill})
