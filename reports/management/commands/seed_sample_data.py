from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Profile
from reports.models import Intervention, Report
from students.models import AcademicRecord, Student


User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with sample students, academic records, reports, and interventions."

    def handle(self, *args, **kwargs):
        try:
            professor = User.objects.get(username="professor")
            counselor = User.objects.get(username="counselor")
        except User.DoesNotExist as exc:
            raise CommandError(
                'Required users are missing. Run "python manage.py seed_users" first.'
            ) from exc

        if getattr(professor.profile, "role", None) != Profile.Role.PROFESSOR:
            raise CommandError('User "professor" does not have the Professor role.')
        if getattr(counselor.profile, "role", None) != Profile.Role.COUNSELOR:
            raise CommandError('User "counselor" does not have the Counselor role.')

        students_data = [
            {
                "student": {
                    "student_id": "2024-0001",
                    "first_name": "Alyssa",
                    "last_name": "Reyes",
                    "course": "BS Information Technology",
                    "year_level": 1,
                },
                "record": {"grade": 91.5, "attendance": 97.0, "behavioral_incidents": "None", "participation": "Good"},
                "reports": [],
            },
            {
                "student": {
                    "student_id": "2024-0002",
                    "first_name": "Marco",
                    "last_name": "Santos",
                    "course": "BS Computer Science",
                    "year_level": 2,
                },
                "record": {"grade": 78.0, "attendance": 83.0, "behavioral_incidents": "Minor", "participation": "Occasional missing"},
                "reports": [
                    {
                        "concern": "Student has shown a gradual decline in quiz scores and has missed several laboratory activities. Monitoring is recommended before the issue worsens.",
                        "status": Report.Status.PENDING,
                    }
                ],
            },
            {
                "student": {
                    "student_id": "2024-0003",
                    "first_name": "Janelle",
                    "last_name": "Cruz",
                    "course": "BS Psychology",
                    "year_level": 3,
                },
                "record": {"grade": 72.5, "attendance": 76.0, "behavioral_incidents": "Severe", "participation": "Frequent missing"},
                "reports": [
                    {
                        "concern": "Student is currently at high risk due to low attendance, failing marks, and repeated classroom behavior concerns.",
                        "status": Report.Status.ONGOING,
                        "interventions": [
                            {
                                "action_taken": "Initial counseling session completed. Student was advised on attendance recovery and referred for weekly monitoring.",
                                "follow_up_date": date.today() + timedelta(days=7),
                                "status_update": Report.Status.ONGOING,
                            }
                        ],
                    }
                ],
            },
            {
                "student": {
                    "student_id": "2024-0004",
                    "first_name": "Kevin",
                    "last_name": "Lopez",
                    "course": "BS Information Systems",
                    "year_level": 4,
                },
                "record": {"grade": 68.0, "attendance": 70.0, "behavioral_incidents": "None", "participation": "No participation"},
                "reports": [
                    {
                        "concern": "Student is at risk of failing the term after multiple absences and a sharp drop in academic performance.",
                        "status": Report.Status.RESOLVED,
                        "interventions": [
                            {
                                "action_taken": "Met with the student and coordinated a catch-up plan with subject instructors.",
                                "follow_up_date": date.today() - timedelta(days=14),
                                "status_update": Report.Status.ONGOING,
                            },
                            {
                                "action_taken": "Follow-up confirmed improved attendance and completed remediation tasks.",
                                "follow_up_date": date.today() - timedelta(days=3),
                                "status_update": Report.Status.RESOLVED,
                            },
                        ],
                    }
                ],
            },
            {
                "student": {
                    "student_id": "2024-0005",
                    "first_name": "Bianca",
                    "last_name": "Navarro",
                    "course": "BS Accountancy",
                    "year_level": 2,
                },
                "record": {"grade": 85.0, "attendance": 79.0, "behavioral_incidents": "None", "participation": "Good"},
                "reports": [
                    {
                        "concern": "Attendance dropped below the expected threshold. Student may need outreach before this affects performance further.",
                        "status": Report.Status.PENDING,
                    }
                ],
            },
            {
                "student": {
                    "student_id": "2024-0006",
                    "first_name": "Daniel",
                    "last_name": "Garcia",
                    "course": "BS Civil Engineering",
                    "year_level": 1,
                },
                "record": {"grade": 74.0, "attendance": 88.0, "behavioral_incidents": "Moderate", "participation": "Good"},
                "reports": [
                    {
                        "concern": "Student is passing irregularly and has been involved in repeated minor conduct incidents reported by faculty.",
                        "status": Report.Status.ONGOING,
                        "interventions": [
                            {
                                "action_taken": "Behavior contract discussed with the student and guardian contact was documented.",
                                "follow_up_date": date.today() + timedelta(days=10),
                                "status_update": Report.Status.ONGOING,
                            }
                        ],
                    }
                ],
            },
            {
                "student": {
                    "student_id": "2024-0007",
                    "first_name": "Patricia",
                    "last_name": "Fernandez",
                    "course": "BS Nursing",
                    "year_level": 3,
                },
                "record": {"grade": 89.0, "attendance": 92.0, "behavioral_incidents": "None", "participation": "Good"},
                "reports": [],
            },
            {
                "student": {
                    "student_id": "2024-0008",
                    "first_name": "Rafael",
                    "last_name": "Mendoza",
                    "course": "BS Hospitality Management",
                    "year_level": 4,
                },
                "record": {"grade": 73.0, "attendance": 77.0, "behavioral_incidents": "Minor", "participation": "Occasional missing"},
                "reports": [
                    {
                        "concern": "Student has both low attendance and below-threshold grades and should be prioritized for counselor review.",
                        "status": Report.Status.PENDING,
                    }
                ],
            },
        ]

        created_students = 0
        created_reports = 0
        created_interventions = 0

        with transaction.atomic():
            for entry in students_data:
                student_defaults = entry["student"].copy()
                student_id = student_defaults.pop("student_id")
                student, student_created = Student.objects.get_or_create(
                    student_id=student_id,
                    defaults=student_defaults,
                )

                if student_created:
                    created_students += 1

                AcademicRecord.objects.update_or_create(
                    student=student,
                    defaults=entry["record"],
                )

                for report_data in entry["reports"]:
                    concern = report_data["concern"]
                    report, report_created = Report.objects.get_or_create(
                        student=student,
                        professor=professor,
                        concern=concern,
                        defaults={"status": report_data["status"]},
                    )

                    if not report_created and report.status != report_data["status"]:
                        report.status = report_data["status"]
                        report.save(update_fields=["status"])

                    if report_created:
                        created_reports += 1

                    for intervention_data in report_data.get("interventions", []):
                        intervention, intervention_created = Intervention.objects.get_or_create(
                            report=report,
                            counselor=counselor,
                            action_taken=intervention_data["action_taken"],
                            defaults={
                                "follow_up_date": intervention_data["follow_up_date"],
                                "status_update": intervention_data["status_update"],
                            },
                        )
                        if not intervention_created:
                            intervention.follow_up_date = intervention_data["follow_up_date"]
                            intervention.status_update = intervention_data["status_update"]
                            intervention.save(update_fields=["follow_up_date", "status_update"])
                        else:
                            created_interventions += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sample data ready. Students created: {created_students}, "
                f"reports created: {created_reports}, interventions created: {created_interventions}."
            )
        )
