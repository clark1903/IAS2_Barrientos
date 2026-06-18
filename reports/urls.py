from django.urls import path

from .views import (
    CounselorReportListView,
    ProfessorReportListView,
    ReportCreateView,
    ReportPdfDownloadView,
    ReportDetailView,
    ReportStatusUpdateView,
    StudentReportListView,
    add_intervention,
    add_case_comment,
)

app_name = "reports"


urlpatterns = [
    path("mine/", ProfessorReportListView.as_view(), name="mine"),
    path("cases/", CounselorReportListView.as_view(), name="cases"),
    path("student/<int:student_pk>/", StudentReportListView.as_view(), name="student_reports"),
    path("student/<int:student_pk>/add/", ReportCreateView.as_view(), name="add"),
    path("<int:pk>/", ReportDetailView.as_view(), name="detail"),
    path("<int:pk>/pdf/", ReportPdfDownloadView.as_view(), name="pdf"),
    path("<int:pk>/status/", ReportStatusUpdateView.as_view(), name="status"),
    path("<int:pk>/interventions/add/", add_intervention, name="add_intervention"),
    path("<int:pk>/comments/add/", add_case_comment, name="add_case_comment"),
]

