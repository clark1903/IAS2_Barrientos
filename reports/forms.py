from django import forms

from .models import CaseComment, Intervention, Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["concern"]
        widgets = {
            "concern": forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "Describe the concern..."}),
        }


class ReportStatusForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class InterventionForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = ["action_taken", "follow_up_date", "status_update"]
        widgets = {
            "action_taken": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Intervention notes / action taken..."}),
            "follow_up_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status_update": forms.Select(attrs={"class": "form-select"}),
        }


class CaseCommentForm(forms.ModelForm):
    class Meta:
        model = CaseComment
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Type a message..."}),
        }
