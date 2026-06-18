from django.urls import path

from .views import admin_dashboard, counselor_dashboard, professor_dashboard

app_name = "dashboard"


urlpatterns = [
    path("admin/", admin_dashboard, name="admin"),
    path("professor/", professor_dashboard, name="professor"),
    path("counselor/", counselor_dashboard, name="counselor"),
]

