from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import Profile
from students.models import Student

from .forms import CaseCommentForm, InterventionForm, ReportForm, ReportStatusForm
from .models import CaseComment, Report


class ReportCreateView(RoleRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    allowed_roles = (Profile.Role.PROFESSOR, Profile.Role.ADMIN)

    def dispatch(self, request, *args, **kwargs):
        self.student = get_object_or_404(Student, pk=kwargs["student_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["student"] = self.student
        return ctx

    def form_valid(self, form):
        form.instance.student = self.student
        form.instance.professor = self.request.user
        resp = super().form_valid(form)
        messages.success(self.request, "Report submitted successfully.")
        return resp

    def get_success_url(self):
        return reverse_lazy("reports:detail", kwargs={"pk": self.object.pk})


class ProfessorReportListView(RoleRequiredMixin, ListView):
    model = Report
    template_name = "reports/professor_report_list.html"
    context_object_name = "reports"
    paginate_by = 10
    allowed_roles = (Profile.Role.PROFESSOR, Profile.Role.ADMIN)

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("student", "professor")
            .prefetch_related("interventions")
        )

        if not (self.request.user.is_superuser or self.request.user.is_staff):
            qs = qs.filter(professor=self.request.user)

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(student__student_id__icontains=q)
                | Q(student__first_name__icontains=q)
                | Q(student__last_name__icontains=q)
                | Q(status__icontains=q)
            )
        return qs


class CounselorReportListView(RoleRequiredMixin, ListView):
    model = Report
    template_name = "reports/counselor_report_list.html"
    context_object_name = "reports"
    paginate_by = 10
    allowed_roles = (Profile.Role.COUNSELOR, Profile.Role.ADMIN)

    def get_queryset(self):
        qs = super().get_queryset().select_related("student", "professor")
        status = self.request.GET.get("status", "").strip()
        if status in {Report.Status.PENDING, Report.Status.ONGOING, Report.Status.RESOLVED}:
            qs = qs.filter(status=status)

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(student__student_id__icontains=q)
                | Q(student__first_name__icontains=q)
                | Q(student__last_name__icontains=q)
                | Q(professor__username__icontains=q)
            )
        return qs


class ReportDetailView(RoleRequiredMixin, DetailView):
    model = Report
    template_name = "reports/report_detail.html"
    context_object_name = "report"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR, Profile.Role.COUNSELOR)

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("student", "professor")
            .prefetch_related("interventions", "interventions__counselor", "comments", "comments__author")
        )
        role = getattr(getattr(self.request.user, "profile", None), "role", None)
        is_admin = self.request.user.is_superuser or self.request.user.is_staff
        if not is_admin and role == Profile.Role.PROFESSOR:
            qs = qs.filter(professor=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report = self.object
        role = getattr(getattr(self.request.user, "profile", None), "role", None)
        is_admin = self.request.user.is_superuser or self.request.user.is_staff
        can_counsel = is_admin or role in {Profile.Role.COUNSELOR, Profile.Role.ADMIN}

        ctx["can_counsel"] = can_counsel
        ctx["status_form"] = ReportStatusForm(instance=report)
        ctx["intervention_form"] = InterventionForm()
        ctx["comment_form"] = CaseCommentForm()
        return ctx


class ReportStatusUpdateView(RoleRequiredMixin, UpdateView):
    model = Report
    form_class = ReportStatusForm
    template_name = "reports/report_status_form.html"
    allowed_roles = (Profile.Role.COUNSELOR, Profile.Role.ADMIN)

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Report status updated.")
        return resp

    def get_success_url(self):
        return reverse_lazy("reports:detail", kwargs={"pk": self.object.pk})


class ReportPdfDownloadView(RoleRequiredMixin, View):
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR, Profile.Role.COUNSELOR)

    def get_queryset(self):
        qs = Report.objects.select_related("student", "professor", "student__academic_record").prefetch_related(
            "interventions", "interventions__counselor"
        )
        role = getattr(getattr(self.request.user, "profile", None), "role", None)
        is_admin = self.request.user.is_superuser or self.request.user.is_staff
        if not is_admin and role == Profile.Role.PROFESSOR:
            qs = qs.filter(professor=self.request.user)
        return qs

    def get_report(self, pk: int) -> Report:
        return get_object_or_404(self.get_queryset(), pk=pk)

    def get(self, request, *args, **kwargs):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        report = self.get_report(kwargs["pk"])
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="case-report-{report.student.student_id}-{report.pk}.pdf"'
        )

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            leftMargin=0.7 * inch,
            rightMargin=0.7 * inch,
            topMargin=0.7 * inch,
            bottomMargin=0.7 * inch,
        )
        styles = getSampleStyleSheet()
        body_style = styles["BodyText"]
        body_style.spaceAfter = 8
        body_style.leading = 14
        section_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#0f4c81"),
            spaceBefore=8,
            spaceAfter=8,
        )
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=18,
            textColor=colors.HexColor("#12344d"),
            spaceAfter=12,
        )
        meta_label_style = ParagraphStyle(
            "MetaLabel",
            parent=body_style,
            fontName="Helvetica-Bold",
        )

        student = report.student
        record = getattr(student, "academic_record", None)
        interventions = list(report.interventions.all())
        is_ai_generated = report.concern.startswith("[AI GENERATED REPORT]")

        story = [
            Paragraph("InsightEdge Student Case File", title_style),
            Paragraph(
                f"Generated for {student.full_name} on report #{report.pk}.",
                body_style,
            ),
            Paragraph(
                f"<b>Report Generated At:</b> {timezone.localtime(timezone.now()).strftime('%b %d, %Y %I:%M %p')}",
                body_style,
            ),
            Spacer(1, 6),
        ]

        summary_rows = [
            [
                Paragraph("<b>Student Name</b>", meta_label_style),
                student.full_name,
                Paragraph("<b>Student ID</b>", meta_label_style),
                student.student_id,
            ],
            [
                Paragraph("<b>Course</b>", meta_label_style),
                student.course,
                Paragraph("<b>Year Level</b>", meta_label_style),
                str(student.year_level),
            ],
            [
                Paragraph("<b>Professor</b>", meta_label_style),
                report.professor.get_full_name() or report.professor.username,
                Paragraph("<b>Submitted</b>", meta_label_style),
                timezone.localtime(report.date_submitted).strftime("%b %d, %Y %I:%M %p"),
            ],
            [
                Paragraph("<b>Case Status</b>", meta_label_style),
                report.status,
                Paragraph("<b>AI Generated</b>", meta_label_style),
                "Yes" if is_ai_generated else "No",
            ],
        ]

        summary_table = Table(summary_rows, colWidths=[1.1 * inch, 2.2 * inch, 1.1 * inch, 2.2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef4fb")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d8e8")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8e2ee")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.extend([summary_table, Spacer(1, 12)])

        story.append(Paragraph("Academic Record", section_style))
        if record:
            record_rows = [
                ["Grade", f"{record.grade:.2f}"],
                ["Attendance", f"{record.attendance:.2f}%"],
                ["Behavioral Incidents", record.behavioral_incidents],
                ["Participation Status", record.participation],
                ["Risk Score", str(record.risk_score)],
                ["Risk Level", record.risk_level],
            ]
            record_table = Table(record_rows, colWidths=[1.7 * inch, 4.9 * inch])
            record_table.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d8e8")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8e2ee")),
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f7f9fc")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.extend([record_table, Spacer(1, 12)])
        else:
            story.extend([Paragraph("No academic record is available for this student.", body_style), Spacer(1, 12)])

        story.append(Paragraph("Case Narrative", section_style))
        story.extend(
            [
                Paragraph(escape(report.concern).replace("\n", "<br/>"), body_style),
                Spacer(1, 12),
            ]
        )

        if interventions:
            story.append(Paragraph("Interventions", section_style))
            for index, intervention in enumerate(interventions, start=1):
                follow_up = (
                    intervention.follow_up_date.strftime("%b %d, %Y")
                    if intervention.follow_up_date
                    else "No follow-up date"
                )
                story.extend(
                    [
                        Paragraph(
                            (
                                f"<b>{index}. Counselor:</b> "
                                f"{escape(intervention.counselor.get_full_name() or intervention.counselor.username)}"
                                f" | <b>Status:</b> {escape(intervention.status_update)}"
                                f" | <b>Logged:</b> {timezone.localtime(intervention.created_at).strftime('%b %d, %Y %I:%M %p')}"
                            ),
                            body_style,
                        ),
                        Paragraph(f"<b>Follow-up:</b> {follow_up}", body_style),
                        Paragraph(escape(intervention.action_taken).replace('\n', '<br/>'), body_style),
                        Spacer(1, 8),
                    ]
                )
        else:
            story.extend([Paragraph("No interventions have been recorded for this case yet.", body_style)])

        doc.build(story)
        return response


def add_intervention(request, pk: int):
    """
    Counselors add intervention notes; report status can be updated via the intervention entry.
    """
    report = get_object_or_404(Report.objects.select_related("student", "professor"), pk=pk)
    role = getattr(getattr(request.user, "profile", None), "role", None)
    is_admin = request.user.is_superuser or request.user.is_staff
    if not request.user.is_authenticated or (not is_admin and role not in {Profile.Role.COUNSELOR, Profile.Role.ADMIN}):
        messages.error(request, "You do not have permission to add an intervention.")
        return redirect("accounts:login")

    if request.method != "POST":
        return redirect("reports:detail", pk=report.pk)

    form = InterventionForm(request.POST)
    if form.is_valid():
        intervention = form.save(commit=False)
        intervention.report = report
        intervention.counselor = request.user
        intervention.save()
        # Keep report status in sync with the latest intervention update.
        report.status = intervention.status_update
        report.save(update_fields=["status"])
        messages.success(request, "Intervention note added.")
    else:
        messages.error(request, "Please correct the errors in the intervention form.")
    return redirect("reports:detail", pk=report.pk)



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

class StudentReportListView(RoleRequiredMixin, ListView):
    model = Report
    template_name = "reports/student_report_list.html"
    context_object_name = "reports"
    paginate_by = 10
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR, Profile.Role.COUNSELOR)

    def dispatch(self, request, *args, **kwargs):
        self.student = get_object_or_404(Student, pk=kwargs["student_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().select_related("student", "professor").filter(student=self.student)
        role = getattr(getattr(self.request.user, "profile", None), "role", None)
        is_admin = self.request.user.is_superuser or self.request.user.is_staff
        if not is_admin and role == Profile.Role.PROFESSOR:
            qs = qs.filter(professor=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["student"] = self.student
        return ctx

