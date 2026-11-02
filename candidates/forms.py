from django import forms

from .models import Candidate

INPUT = "input input-bordered w-full"


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ["first_name", "last_name", "email", "phone", "source", "notes"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": INPUT}),
            "last_name": forms.TextInput(attrs={"class": INPUT}),
            "email": forms.EmailInput(attrs={"class": INPUT}),
            "phone": forms.TextInput(attrs={"class": INPUT}),
            "source": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "notes": forms.Textarea(
                attrs={"class": "textarea textarea-bordered w-full", "rows": 4}
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        others = Candidate.objects.exclude(pk=self.instance.pk)
        if others.filter(email__iexact=email).exists():
            raise forms.ValidationError("A candidate with this email already exists.")
        return email
