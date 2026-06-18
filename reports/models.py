from django.conf import settings
from django.db import models

from students.models import Student


class Report(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        ONGOING = "Ongoing", "Ongoing"
        RESOLVED = "Resolved", "Resolved"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="reports")
    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submitted_reports")
    concern = models.TextField()
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ("-date_submitted",)

    def __str__(self) -> str:
        return f"Report({self.student.student_id}, {self.status})"


class Intervention(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="interventions")
    counselor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interventions")
    action_taken = models.TextField()
    follow_up_date = models.DateField(null=True, blank=True)
    status_update = models.CharField(max_length=20, choices=Report.Status.choices, default=Report.Status.ONGOING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Intervention({self.report_id}, {self.status_update})"


class CaseComment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="report_comments")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Comment by {self.author.username} on Report #{self.report_id}"
