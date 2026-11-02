from django import forms

from .models import Skill


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "input input-bordered w-full"})}

    def clean_name(self):
        name = self.cleaned_data["name"]
        others = Skill.objects.exclude(pk=self.instance.pk)
        if others.filter(name__iexact=name).exists():
            raise forms.ValidationError("A skill with this name already exists.")
        return name
