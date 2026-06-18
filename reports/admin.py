from django.contrib import admin

from .models import Intervention, Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("student", "professor", "status", "date_submitted")
    list_filter = ("status", "date_submitted")
    search_fields = ("student__student_id", "student__first_name", "student__last_name", "professor__username")
    list_select_related = ("student", "professor")


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ("report", "counselor", "status_update", "follow_up_date", "created_at")
    list_filter = ("status_update", "created_at")
    search_fields = ("report__student__student_id", "counselor__username")
    list_select_related = ("report", "counselor")

