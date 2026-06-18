from django import forms

from .models import AcademicRecord, Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["student_id", "first_name", "last_name", "course", "year_level"]
        widgets = {
            "student_id": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "course": forms.TextInput(attrs={"class": "form-control"}),
            "year_level": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }


class AcademicRecordForm(forms.ModelForm):
    class Meta:
        model = AcademicRecord
        fields = ["grade", "attendance", "behavioral_incidents", "participation"]
        widgets = {
            "grade": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": 0, "max": 100, "required": "required"}),
            "attendance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": 0, "max": 100, "required": "required"}),
            "behavioral_incidents": forms.Select(attrs={"class": "form-select", "required": "required"}),
            "participation": forms.Select(attrs={"class": "form-select", "required": "required"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If the record has 0.0 from an old ghost save, wipe it so the box is totally empty
        if self.instance and self.instance.pk:
            if self.instance.grade == 0.0 and self.instance.attendance == 0.0:
                self.initial['grade'] = None
                self.initial['attendance'] = None

        # If it's a new unsaved record, ensure it starts empty
        if not self.instance.pk:
            self.initial['grade'] = None
            self.initial['attendance'] = None
            self.initial['behavioral_incidents'] = ""
            self.initial['participation'] = ""

        # Force a blank standard option so they have to open the dropdown
        behavior_choices = list(self.fields['behavioral_incidents'].choices)
        # Remove empty or duplicate blank choices if they exist, then prepend a strict one
        behavior_choices = [c for c in behavior_choices if c[0] != ""]
        self.fields['behavioral_incidents'].choices = [("", "--- Select Behavior ---")] + behavior_choices

        part_choices = list(self.fields['participation'].choices)
        part_choices = [c for c in part_choices if c[0] != ""]
        self.fields['participation'].choices = [("", "--- Select Participation ---")] + part_choices

        # Strict backend enforcement
        self.fields['grade'].required = True
        self.fields['attendance'].required = True
        self.fields['behavioral_incidents'].required = True
        self.fields['participation'].required = True

class StudentCSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV File",
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".csv"}),
        help_text="File must be a CSV containing headers: student_id, first_name, last_name, course, year_level."
    )

