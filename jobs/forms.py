from django import forms

from .models import JobOpening


class JobOpeningForm(forms.ModelForm):
    class Meta:
        model = JobOpening
        fields = ["title", "department", "description", "skills"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "department": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "description": forms.Textarea(
                attrs={"class": "textarea textarea-bordered w-full", "rows": 6}
            ),
            "skills": forms.CheckboxSelectMultiple(attrs={"class": "checkbox checkbox-sm"}),
        }
