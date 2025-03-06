from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# Create your models here.
class User(AbstractUser):
    pass
    


class Report(models.Model):
    """Model for student progress reports"""
    REPORT_TYPES = (
        ('3-month', '3-Month Progress Report'),
        ('6-month', '6-Month Progress Report'),
        ('annual', 'Annual Report'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    review_date = models.DateTimeField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()}) - {self.student.username}"
    
    class Meta:
        ordering = ['-created_at']
        
        

class HelpRequest(models.Model):
    """Model for help requests, bug reports, and feature requests"""
    REQUEST_TYPES = (
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('help', 'Help Request'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    subject = models.CharField(max_length=255)
    message = models.TextField()
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='help_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    attachment = models.FileField(upload_to='help_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='help_responses')
    response_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_request_type_display()}: {self.subject} - {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']