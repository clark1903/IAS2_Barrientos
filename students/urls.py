from django.urls import path

from .views import (
    AcademicRecordUpsertView,
    StudentCreateView,
    StudentDeleteView,
    StudentDetailView,
    StudentListView,
    StudentUpdateView,
    StudentCSVUploadView,
    generate_ai_report,
)

app_name = "students"


urlpatterns = [
    path("", StudentListView.as_view(), name="list"),
    path("add/", StudentCreateView.as_view(), name="add"),
    path("import-csv/", StudentCSVUploadView.as_view(), name="import_csv"),
    path("<int:pk>/", StudentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", StudentUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", StudentDeleteView.as_view(), name="delete"),
    path("<int:pk>/ai-report/", generate_ai_report, name="generate_ai_report"),
    path("<int:student_pk>/academic-record/", AcademicRecordUpsertView.as_view(), name="academic_edit"),
]
