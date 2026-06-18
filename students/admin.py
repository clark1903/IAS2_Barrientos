from django.contrib import admin

from .models import AcademicRecord, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "last_name", "first_name", "course", "year_level")
    search_fields = ("student_id", "first_name", "last_name", "course")
    list_filter = ("course", "year_level")


@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "grade", "attendance", "behavioral_incidents", "participation", "risk_score", "risk_level")
    list_select_related = ("student",)
    list_filter = ("risk_level", "behavioral_incidents", "participation")

