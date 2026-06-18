from django.db.models import Count
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import Profile
from reports.models import Report
from students.models import AcademicRecord, Student
from reports.models import Intervention
from django.db.models import Count
import json


@role_required(Profile.Role.ADMIN)
def admin_dashboard(request):
    total_students = Student.objects.count()

    # Count by risk level. Students without academic record are treated separately.
    risk_counts = (
        AcademicRecord.objects.values("risk_level").annotate(total=Count("id")).order_by("risk_level")
    )
    risk_map = {row["risk_level"]: row["total"] for row in risk_counts}

    total_high = risk_map.get("High Risk", 0)
    total_mod = risk_map.get("Moderate Risk", 0)
    total_safe = risk_map.get("Safe", 0)

    chart_labels = ["High Risk", "Moderate Risk", "Safe"]
    chart_values = [total_high, total_mod, total_safe]
    # JSON-encode chart data for safe insertion into JS in the template
    chart_labels_json = json.dumps(chart_labels)
    chart_values_json = json.dumps(chart_values)

    return render(
        request,
        "dashboard/admin_dashboard.html",
        {
            "total_students": total_students,
            "total_high": total_high,
            "total_moderate": total_mod,
            "total_safe": total_safe,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "chart_labels_json": chart_labels_json,
            "chart_values_json": chart_values_json,
        },
    )


@role_required(Profile.Role.PROFESSOR)
def professor_dashboard(request):
    my_reports = Report.objects.filter(professor=request.user).select_related("student").order_by("-date_submitted")[:8]

    students_reported_qs = Student.objects.filter(reports__professor=request.user).distinct().order_by("last_name", "first_name")[:8]

    high_risk_students = (
        Student.objects.filter(academic_record__risk_level="High Risk")
        .select_related("academic_record")
        .order_by("last_name", "first_name")[:8]
    )

    return render(
        request,
        "dashboard/professor_dashboard.html",
        {
            "my_reports": my_reports,
            "students_reported": students_reported_qs,
            "high_risk_students": high_risk_students,
        },
    )


@role_required(Profile.Role.COUNSELOR)
def counselor_dashboard(request):
    pending = Report.objects.filter(status=Report.Status.PENDING).select_related("student", "professor").order_by("-date_submitted")[:8]
    ongoing = Report.objects.filter(status=Report.Status.ONGOING).count()
    resolved = Report.objects.filter(status=Report.Status.RESOLVED).count()
    # Recent interventions across system and counselor's own interventions
    recent_interventions = (
        Intervention.objects.select_related("report", "counselor", "report__student").order_by("-created_at")[:8]
    )
    my_interventions = (
        Intervention.objects.filter(counselor=request.user).select_related("report", "report__student").order_by("-created_at")[:8]
    )

    # Recent reports submitted by professors (all statuses)
    recent_reports = Report.objects.select_related("student", "professor").order_by("-date_submitted")[:8]

    # High-risk students for quick access
    high_risk_students = (
        Student.objects.filter(academic_record__risk_level="High Risk")
        .select_related("academic_record")
        .order_by("last_name", "first_name")[:8]
    )

    # Risk distribution across all students (for counselor overview)
    # (chart removed for counselor dashboard)

    return render(
        request,
        "dashboard/counselor_dashboard.html",
        {
            "pending_reports": pending,
            "ongoing_count": ongoing,
            "resolved_count": resolved,
                "recent_interventions": recent_interventions,
                "my_interventions": my_interventions,
                "recent_reports": recent_reports,
                "high_risk_students": high_risk_students,
            "pending_count": Report.objects.filter(status=Report.Status.PENDING).count(),
        },
    )


