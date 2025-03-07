import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth.models import Group
from web.models import Report, User
from django.forms import modelform_factory

TEMPLATE_DIR = 'report'

@login_required
def report(request):
    user = request.user
    user_groups = [g.name for g in user.groups.all()]
    
    # Determine the current user's role
    is_student = 'student_group' in user_groups
    is_teacher = 'teacher_group' in user_groups
    is_admin = 'admin_group' in user_groups or 'superadmin_group' in user_groups
    
    # Get reports based on role
    if is_admin:
        # Admins and superadmins see all reports
        reports = Report.objects.all().order_by('-created_at')
        teachers = User.objects.filter(groups__name='teacher_group')
    elif is_teacher:
        # Teachers see reports assigned to them
        reports = Report.objects.filter(assigned_to=user).order_by('-created_at')
        teachers = None
    else:
        # Students see only their own reports
        reports = Report.objects.filter(student=user).order_by('-created_at')
        teachers = None
    
    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Add new report (student)
        if action == 'add_report' and is_student:
            ReportForm = modelform_factory(
                Report, 
                fields=['title', 'description', 'report_type', 'file', 'due_date']
            )
            form = ReportForm(request.POST, request.FILES)
            if form.is_valid():
                report = form.save(commit=False)
                report.student = user
                report.status = 'submitted'
                report.submitted_at = timezone.now()
                report.save()
                messages.success(request, 'Report submitted successfully')
                return redirect('report')
        
        # Update existing report (student)
        elif action == 'update_report' and is_student:
            report_id = request.POST.get('report_id')
            report = get_object_or_404(Report, id=report_id, student=user)
            
            # Only allow updates if report is in draft or rejected state
            if report.status in ['draft', 'rejected']:
                ReportForm = modelform_factory(
                    Report, 
                    fields=['title', 'description', 'report_type', 'file', 'due_date']
                )
                form = ReportForm(request.POST, request.FILES, instance=report)
                if form.is_valid():
                    updated_report = form.save(commit=False)
                    updated_report.status = 'submitted'
                    updated_report.submitted_at = timezone.now()
                    updated_report.save()
                    messages.success(request, 'Report updated and resubmitted successfully')
                    return redirect('report')
            else:
                messages.error(request, 'You can only update reports in draft or rejected status')
        
        # Approve report (teacher)
        elif action == 'approve_report' and is_teacher:
            report_id = request.POST.get('report_id')
            feedback = request.POST.get('feedback')
            report = get_object_or_404(Report, id=report_id, assigned_to=user)
            
            if report.status == 'submitted':
                report.status = 'approved'
                report.feedback = feedback
                report.reviewed_by = user
                report.review_date = timezone.now()
                report.save()
                messages.success(request, 'Report approved successfully')
                return redirect('report')
        
        # Reject report (teacher)
        elif action == 'reject_report' and is_teacher:
            report_id = request.POST.get('report_id')
            feedback = request.POST.get('feedback')
            report = get_object_or_404(Report, id=report_id, assigned_to=user)
            
            if report.status == 'submitted':
                report.status = 'rejected'
                report.feedback = feedback
                report.reviewed_by = user
                report.review_date = timezone.now()
                report.save()
                messages.success(request, 'Report rejected successfully')
                return redirect('report')
        
        # Assign report to teacher (admin)
        elif action == 'assign_report' and is_admin:
            report_id = request.POST.get('report_id')
            teacher_id = request.POST.get('teacher_id')
            
            report = get_object_or_404(Report, id=report_id)
            teacher = get_object_or_404(User, id=teacher_id)
            
            # Check if the assigned user is actually a teacher
            if Group.objects.get(name='teacher_group') in teacher.groups.all():
                report.assigned_to = teacher
                report.save()
                messages.success(request, 'Report assigned successfully')
                return redirect('report')
            else:
                messages.error(request, 'Selected user is not a teacher')
        
        # Delete report (admin or student who owns the report)
        elif action == 'delete_report':
            report_id = request.POST.get('report_id')
            
            if is_admin:
                report = get_object_or_404(Report, id=report_id)
            elif is_student:
                report = get_object_or_404(Report, id=report_id, student=user)
            else:
                return HttpResponseForbidden("You don't have permission to delete this report")
            
            report.delete()
            messages.success(request, 'Report deleted successfully')
            return redirect('report')
    
    context = {
        'reports': reports,
        'is_student': is_student,
        'is_teacher': is_teacher, 
        'is_admin': is_admin,
        'teachers': teachers,
    }
    
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'), context)
