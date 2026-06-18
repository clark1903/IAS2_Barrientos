from django.db import models


class Student(models.Model):
    student_id = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=120)
    year_level = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ("last_name", "first_name")

    def __str__(self) -> str:
        return f"{self.student_id} - {self.last_name}, {self.first_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class AcademicRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="academic_record")
    grade = models.FloatField()
    attendance = models.FloatField(help_text="Attendance percentage (0-100).")
    
    class BehavioralIncidents(models.TextChoices):
        NONE = "None", "None"
        MINOR = "Minor", "Minor (Low Risk): Talking/disruption, not following instructions, tardiness, incomplete assignments"
        MODERATE = "Moderate", "Moderate (Needs Monitoring): Repeated disruption, bullying, cheating, disrespect toward teachers"
        SEVERE = "Severe", "Severe (High Risk): Physical fights, vandalism, substance use, threats or harassment"
        
    class Participation(models.TextChoices):
        GOOD = "Good", "Good"
        OCCASIONAL = "Occasional missing", "Occasional missing"
        FREQUENT = "Frequent missing", "Frequent missing"
        NONE = "No participation", "No participation"

    behavioral_incidents = models.CharField(
        max_length=50, 
        choices=BehavioralIncidents.choices, 
        default=BehavioralIncidents.NONE
    )
    participation = models.CharField(
        max_length=50, 
        choices=Participation.choices, 
        default=Participation.GOOD
    )

    risk_score = models.PositiveSmallIntegerField(default=0, editable=False)
    risk_level = models.CharField(max_length=20, default="Safe", editable=False)

    def __str__(self) -> str:
        return f"AcademicRecord({self.student.student_id})"

    def calculate_risk(self) -> tuple[int, str]:
        # Overall risk is the MAXIMUM tier across all four dimensions.
        tier = 0
        
        # A. Academic Performance
        academic_tier = 0
        if self.grade < 70:
            academic_tier = 3
        elif self.grade <= 74: # 70-74
            academic_tier = 2
        elif self.grade <= 84: # 75-84
            academic_tier = 1
            
        # B. Attendance
        attendance_tier = 0
        absence = 100.0 - self.attendance
        if absence >= 30:
            attendance_tier = 3
        elif absence >= 20: # 20-29%
            attendance_tier = 2
        elif absence >= 10: # 10-19%
            attendance_tier = 1
            
        # C. Behavioral Incidents
        behavior_tier = 0
        if self.behavioral_incidents == self.BehavioralIncidents.SEVERE:
            behavior_tier = 3
        elif self.behavioral_incidents == self.BehavioralIncidents.MODERATE:
            behavior_tier = 2
        elif self.behavioral_incidents == self.BehavioralIncidents.MINOR:
            behavior_tier = 1
            
        # D. Participation
        part_tier = 0
        if self.participation == self.Participation.NONE:
            part_tier = 3
        elif self.participation == self.Participation.FREQUENT:
            part_tier = 2
        elif self.participation == self.Participation.OCCASIONAL:
            part_tier = 1
            
        tier = max(academic_tier, attendance_tier, behavior_tier, part_tier)
        
        if tier >= 3:
            level = "High Risk"
            score = 3
        elif tier == 2:
            level = "Moderate Risk"
            score = 2
        elif tier == 1:
            level = "Low Risk"
            score = 1
        else:
            level = "No Risk"
            score = 0
            
        return score, level

    def save(self, *args, **kwargs):
        # Rule-based "AI" risk computation (no ML).
        score, level = self.calculate_risk()
        self.risk_score = score
        self.risk_level = level
        super().save(*args, **kwargs)

