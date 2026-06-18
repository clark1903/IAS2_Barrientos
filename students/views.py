from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.conf import settings
from django.contrib.auth.decorators import login_required
from reports.models import Report

from accounts.mixins import RoleRequiredMixin
from accounts.models import Profile

from .forms import AcademicRecordForm, StudentForm
from .models import AcademicRecord, Student


import csv
import io
from django.views import View
from django.shortcuts import render
from .forms import StudentCSVUploadForm

class StudentListView(RoleRequiredMixin, ListView):
    model = Student
    template_name = "students/student_list.html"
    context_object_name = "students"
    paginate_by = 10
    # Allow counselors to view the student list (they should be able to review cases).
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR, Profile.Role.COUNSELOR)

    def get_queryset(self):
        qs = super().get_queryset().select_related()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(student_id__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(course__icontains=q)
            )
        return qs


class StudentDetailView(RoleRequiredMixin, DetailView):
    model = Student
    template_name = "students/student_detail.html"
    context_object_name = "student"
    # Counselors should be able to view student details to process cases.
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR, Profile.Role.COUNSELOR)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student = self.object
        record = getattr(student, "academic_record", None)
        ctx["record"] = record
        return ctx


class StudentCreateView(RoleRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR)

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Student created successfully.")
        return resp

    def get_success_url(self):
        return reverse_lazy("students:detail", kwargs={"pk": self.object.pk})


class StudentUpdateView(RoleRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR)

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Student updated successfully.")
        return resp

    def get_success_url(self):
        return reverse_lazy("students:detail", kwargs={"pk": self.object.pk})


class StudentDeleteView(RoleRequiredMixin, DeleteView):
    model = Student
    template_name = "students/student_confirm_delete.html"
    success_url = reverse_lazy("students:list")
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Student deleted successfully.")
        return super().delete(request, *args, **kwargs)


class AcademicRecordUpsertView(RoleRequiredMixin, UpdateView):
    """
    Edit existing academic record; if missing, create one first.
    """

    model = AcademicRecord
    form_class = AcademicRecordForm
    template_name = "students/academic_record_form.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.PROFESSOR)

    def dispatch(self, request, *args, **kwargs):
        self._student = get_object_or_404(Student, pk=kwargs["student_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if hasattr(self._student, "academic_record"):
            return self._student.academic_record
        return AcademicRecord(student=self._student)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["student"] = self._student
        return ctx

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Academic record saved. Risk score and risk level were updated automatically.")
        return resp

    def get_success_url(self):
        return reverse_lazy("students:detail", kwargs={"pk": self._student.pk})

@login_required
def generate_ai_report(request, pk):
    role = getattr(getattr(request.user, "profile", None), "role", None)
    is_admin = request.user.is_superuser or request.user.is_staff
    
    if not is_admin and role not in [Profile.Role.PROFESSOR, Profile.Role.COUNSELOR]:
        messages.error(request, "Only professors, counselors, and admins can generate AI reports.")
        return redirect("students:detail", pk=pk)
        
    student = get_object_or_404(Student, pk=pk)
    record = getattr(student, "academic_record", None)
    
    if not record:
        messages.error(request, "Cannot generate report. Student has no academic record yet.")
        return redirect("students:detail", pk=pk)
        
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "replace_with_your_gemini_api_key":
        messages.error(request, "Gemini API Key is not configured.")
        return redirect("students:detail", pk=pk)
    
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        You are an AI assistant for a school counselor. Based on the student's academic and behavioral data below, write a professional report (2-3 paragraphs) that provides:
        1. An assessment of their current status.
        2. Key insights into potential underlying issues or correlations based on their combined metrics.
        3. Recommended actionable interventions for the counselor.

        Be objective and helpful. Do not include greetings or sign-offs, just the report body.
        
        Student Name: {student.first_name} {student.last_name}
        Course: {student.course}
        Year Level: {student.year_level}
        
        Academic Record:
        Grade: {record.grade}
        Attendance: {record.attendance}%
        Behavioral Incidents: {record.behavioral_incidents}
        Participation: {record.participation}
        System Risk Level Evaluation: {record.risk_level} (Score: {record.risk_score})
        """
        
        response = model.generate_content(prompt)
        ai_text = response.text
        
        # Create the report
        report = Report.objects.create(
            student=student,
            professor=request.user,
            concern=f"[AI GENERATED REPORT]\n{ai_text}",
            status=Report.Status.PENDING
        )
        
        messages.success(request, "AI Report successfully generated and sent to counselors.")
        return redirect("reports:detail", pk=report.pk)
        
    except ImportError as e:
        messages.error(request, f"AI reporting dependency failed to load: {e}")
        return redirect("students:detail", pk=pk)
    except Exception as e:
        messages.error(request, f"Failed to generate AI report: {str(e)}")
        return redirect("students:detail", pk=pk)

class StudentCSVUploadView(RoleRequiredMixin, View):
    template_name = "students/student_csv_upload.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.COUNSELOR, Profile.Role.PROFESSOR)

    def get(self, request):
        form = StudentCSVUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = StudentCSVUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        csv_file = request.FILES["csv_file"]
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "File is not a CSV.")
            return render(request, self.template_name, {"form": form})

        try:
            data_set = csv_file.read().decode("UTF-8")
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)
            
            # Normalize headers (strip whitespace and lower case)
            headers = [h.strip().lower() for h in reader.fieldnames]
            required = ["student_id", "first_name", "last_name", "course", "year_level"]
            # Risk data is optional per row but recommended
            risk_fields = ["grade", "attendance", "behavioral_incidents", "participation"]
            
            for req in required:
                if req not in headers:
                    messages.error(request, f"Missing required column: {req}")
                    return render(request, self.template_name, {"form": form})

            success_count = 0
            error_count = 0
            
            for row in reader:
                try:
                    # Clean the row data (trim whitespace)
                    clean_row = {k.strip().lower(): v.strip() for k, v in row.items()}
                    
                    # 1. Identity Data
                    student, created = Student.objects.update_or_create(
                        student_id=clean_row["student_id"],
                        defaults={
                            "first_name": clean_row["first_name"],
                            "last_name": clean_row["last_name"],
                            "course": clean_row["course"],
                            "year_level": int(clean_row["year_level"]),
                        }
                    )
                    
                    # 2. Risk Data (Academic Record)
                    if all(rf in clean_row for rf in risk_fields):
                        # Map strings to exact choice values if needed (simple case-insensitive match)
                        behavior = clean_row["behavioral_incidents"].capitalize()
                        if behavior not in [c[0] for c in AcademicRecord.BehavioralIncidents.choices]:
                            behavior = AcademicRecord.BehavioralIncidents.NONE

                        participation = clean_row["participation"].capitalize()
                        # Special handling for spaces if Kaggle data uses them differently
                        valid_part = [c[0] for c in AcademicRecord.Participation.choices]
                        if participation not in valid_part:
                            # Try some common variations
                            if "missing" in participation.lower():
                                if "occasional" in participation.lower():
                                    participation = AcademicRecord.Participation.OCCASIONAL
                                elif "frequent" in participation.lower():
                                    participation = AcademicRecord.Participation.FREQUENT
                            elif "no" in participation.lower():
                                participation = AcademicRecord.Participation.NONE
                            else:
                                participation = AcademicRecord.Participation.GOOD

                        AcademicRecord.objects.update_or_create(
                            student=student,
                            defaults={
                                "grade": float(clean_row["grade"]),
                                "attendance": float(clean_row["attendance"]),
                                "behavioral_incidents": behavior,
                                "participation": participation,
                            }
                        )
                    
                    success_count += 1
                except (ValueError, KeyError) as e:
                    error_count += 1
                    continue

            if success_count > 0:
                messages.success(request, f"Successfully processed {success_count} students.")
            if error_count > 0:
                messages.warning(request, f"Skipped {error_count} rows due to data errors.")
                
            return redirect("students:list")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return render(request, self.template_name, {"form": form})
