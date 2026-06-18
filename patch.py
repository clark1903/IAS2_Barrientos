import sys

with open("reports/views.py", "r") as f:
    content = f.read()

content = content.replace(
    "from .forms import InterventionForm, ReportForm, ReportStatusForm\nfrom .models import Report",
    "from .forms import CaseCommentForm, InterventionForm, ReportForm, ReportStatusForm\nfrom .models import CaseComment, Report"
)

content = content.replace(
    'ctx["intervention_form"] = InterventionForm()\n        return ctx',
    'ctx["intervention_form"] = InterventionForm()\n        ctx["comment_form"] = CaseCommentForm()\n        return ctx'
)

new_func = """
def add_case_comment(request, pk: int):
    report = get_object_or_404(Report, pk=pk)
    role = getattr(getattr(request.user, "profile", None), "role", None)
    is_admin = request.user.is_superuser or request.user.is_staff
    if not request.user.is_authenticated:
        return redirect("accounts:login")
        
    if not is_admin and role not in {Profile.Role.COUNSELOR, Profile.Role.ADMIN}:
        if role == Profile.Role.PROFESSOR and report.professor != request.user:
            from django.contrib import messages
            messages.error(request, "You do not have permission to comment on this report.")
            return redirect("reports:mine")

    if request.method != "POST":
        return redirect("reports:detail", pk=report.pk)

    from .forms import CaseCommentForm
    form = CaseCommentForm(request.POST)
    if form.is_valid():
        from django.contrib import messages
        comment = form.save(commit=False)
        comment.report = report
        comment.author = request.user
        comment.save()
        messages.success(request, "Comment added.")
    else:
        from django.contrib import messages
        messages.error(request, "Please enter a valid message.")
    return redirect("reports:detail", pk=report.pk)

class StudentReportListView"""

content = content.replace("class StudentReportListView", new_func)

with open("reports/views.py", "w") as f:
    f.write(content)
