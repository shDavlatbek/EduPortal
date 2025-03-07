from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from datetime import datetime
import os
from django.core.validators import RegexValidator


def profile_picture_path(instance, filename):
    return os.path.join(
        "Profile",
        instance.user.username,
        "Pictures",
        datetime.now().strftime("%Y/%m/%d"),
        filename,
    )

def certificate_path(instance, filename):
    return os.path.join(
        "Profile",
        instance.user.username,
        "Certificates",
        datetime.now().strftime("%Y/%m/%d"),
        filename,
    )

def article_path(instance, filename):
    return os.path.join(
        "Profile",
        instance.user.username,
        "Articles",
        datetime.now().strftime("%Y/%m/%d"),
        filename,
    )

def report_path(instance, filename):
    return os.path.join(
        "Profile",
        instance.student.username,
        "Reports",
        datetime.now().strftime("%Y/%m/%d"),
        filename,
    )

def help_attachment_path(instance, filename):
    return os.path.join(    
        "Profile",
        instance.user.username,
        "Help",
        datetime.now().strftime("%Y/%m/%d"),
        filename,
    )

def dissertation_path(instance, filename):
    return os.path.join(
        "Profile",
        instance.user.username,
        "Dissertations",
        datetime.now().strftime("%Y/%m/%d"),
        filename,
    )


GENDER_CHOICES = (
    ("male", _("male")),
    ("female", _("female")),
)

EDUCATION_CHOICES = (
    ("intern", _("intern_researcher")),
    ("phd", _("phd")),
    ("dsc", _("dsc")),
    ("independent_phd", _("independent_phd")),
    ("independent_dsc", _("independent_dsc")),
)

REPORT_TYPES = (
    ("3-month", _("3-month")),
    ("6-month", _("6-month")),
    ("annual", _("annual")),
    ("other", _("other")),
)

REPORT_STATUS_CHOICES = (
    ("draft", _("draft")),
    ("pending", _("pending")),
    ("submitted", _("submitted")),
    ("under_review", _("under_review")),
    ("approved", _("approved")),
    ("rejected", _("rejected")),
)


REQUEST_TYPES = (
    ("bug", _("bug")),
    ("feature", _("feature")),
    ("help", _("help")),
    ("other", _("other")),
)

REQUEST_STATUS_CHOICES = (
    ("open", _("open")),
    ("in_progress", _("in_progress")),
    ("resolved", _("resolved")),
    ("closed", _("closed")),
)

ARTICLE_TYPES = (
    ("republic_scientific_journal", _("republic_scientific_journal")),
    ("foreign_scientific_journal", _("foreign_scientific_journal")),
    ("republic_conference_journal", _("republic_conference_journal")),
    ("foreign_conference_journal", _("foreign_conference_journal")),
)


class PassportNumberValidator(RegexValidator):
    # AA1234567
    regex = r"^[A-Z]{2}\d{7}$"
    message = _("enter_valid_passport_number")


class User(AbstractUser):
    pass


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255, blank=True, null=True)
    picture = models.ImageField(
        upload_to=profile_picture_path,
        blank=True,
        null=True,
        default=os.path.join("Profile", "_Default", "default.png"),
    )
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=255, blank=True, null=True, choices=GENDER_CHOICES
    )
    birth_place = models.CharField(max_length=255, blank=True, null=True)
    living_place = models.CharField(max_length=255, blank=True, null=True)
    passport_number = models.CharField(
        max_length=9, blank=True, null=True, validators=[PassportNumberValidator]
    )


class EducationProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="edu_profile"
    )

    # Bachelor
    bachelor_major = models.CharField(max_length=255, blank=True, null=True)
    bachelor_diploma = models.CharField(max_length=255, blank=True, null=True)
    bachelor_diploma_date = models.DateField(blank=True, null=True)

    # Master
    master_major = models.CharField(max_length=255, blank=True, null=True)
    master_diploma = models.CharField(max_length=255, blank=True, null=True)
    master_diploma_date = models.DateField(blank=True, null=True)

    # Next Education
    next_education = models.CharField(
        max_length=255, blank=True, null=True, choices=EDUCATION_CHOICES
    )
    next_education_level = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=(
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
        ),
    )
    next_education_major = models.ForeignKey(
        'NextEducationMajor', on_delete=models.CASCADE, related_name="next_education_majors",
        blank=True,
        null=True,
    )
    
    # Teacher
    teacher_full_name = models.CharField(max_length=255, blank=True, null=True)
    teacher_degree = models.CharField(max_length=255, blank=True, null=True)
    teacher_academic_rank = models.CharField(max_length=255, blank=True, null=True)
    teacher_work_place_position = models.CharField(max_length=255, blank=True, null=True)
    order_number = models.CharField(max_length=255, blank=True, null=True)
    order_date = models.DateField(blank=True, null=True)


class Article(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="articles"
    )
    article_type = models.CharField(max_length=255, choices=ARTICLE_TYPES)
    article_number = models.CharField(max_length=255, blank=True, null=True)
    article_date = models.DateField(blank=True, null=True)
    article_file = models.FileField(upload_to=article_path, blank=True, null=True)


class LanguageCertificate(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="language_certificates"
    )
    certificate_name = models.CharField(max_length=255)
    certificate_date = models.DateField(blank=True, null=True)
    certificate_file = models.FileField(upload_to=certificate_path, blank=True, null=True)

class Dissertation(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="dissertation"
    )
    dissertation_title = models.CharField(max_length=500)
    dissertation_progress = models.IntegerField(default=0)
    dissertation_file = models.FileField(upload_to=dissertation_path, blank=True, null=True)

class NextEducationMajor(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Report(models.Model):
    """Model for student progress reports"""

    title = models.CharField(max_length=255)
    description = models.TextField()
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="student_reports"
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    status = models.CharField(
        max_length=20, choices=REPORT_STATUS_CHOICES, default="draft"
    )
    file = models.FileField(upload_to=report_path, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_reports",
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_reports",
    )
    review_date = models.DateTimeField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return (
            f"{self.title} ({self.get_report_type_display()}) - {self.student.username}"
        )

    class Meta:
        ordering = ["-created_at"]


class HelpRequest(models.Model):
    """Model for help requests, bug reports, and feature requests"""

    subject = models.CharField(max_length=255)
    message = models.TextField()
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="help_requests"
    )
    status = models.CharField(
        max_length=20, choices=REQUEST_STATUS_CHOICES, default="open"
    )

    attachment = models.FileField(upload_to=help_attachment_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="help_responses",
    )
    response_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return (
            f"{self.get_request_type_display()}: {self.subject} - {self.user.username}"
        )

    class Meta:
        ordering = ["-created_at"]
