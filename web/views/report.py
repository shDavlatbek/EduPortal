import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth.models import Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from web.models import Report, User, Profile
from django.forms import modelform_factory
from django.utils.translation import gettext as _
import os.path
from transliterate import translit
TEMPLATE_DIR = 'report'

# Define allowed file extensions
ALLOWED_FILE_EXTENSIONS = [
    # Documents
    'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
    # Spreadsheets
    'xls', 'xlsx', 'ods', 'csv',
    # Presentations
    'ppt', 'pptx', 'odp',
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
    # Archives
    'zip', 'rar', '7z',
]

# Maximum file size (100MB in bytes)
MAX_FILE_SIZE = 100 * 1024 * 1024

def validate_report_file(file):
    """
    Validates uploaded report files
    
    Args:
        file: The uploaded file object
    
    Returns:
        A tuple (is_valid, error_message)
    """
    if not file:
        return True, None
        
    # Check if file is empty (0 bytes)
    if file.size == 0:
        return False, _("uploaded_file_is_empty_upload_valid_file")
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        return False, _("file_size_exceeds_limit_upload_smaller_file")
    
    # Check file extension
    _, ext = os.path.splitext(file.name)
    if ext.startswith('.'):
        ext = ext[1:]
    if ext.lower() not in ALLOWED_FILE_EXTENSIONS:
        formatted_extensions = ', '.join(['.' + ext for ext in ALLOWED_FILE_EXTENSIONS])
        return False, _("this_file_type_is_not_allowed_extensions") + formatted_extensions
    
    return True, None

@login_required
def report(request):
    user = request.user
    user_groups = [g.name for g in user.groups.all()]
    
    # Determine the current user's role
    is_student = 'student_group' in user_groups
    is_teacher = 'teacher_group' in user_groups
    is_admin = 'admin_group' in user_groups or 'superadmin_group' in user_groups
    
    # Auto-approve reports past due date
    auto_approve_reports(is_admin)
    
    # Get filter parameters
    filter_status = request.GET.get('status')
    search_query = request.GET.get('search')
    search_field = request.GET.get('search_field', 'all')
    
    # Current datetime for comparison with due dates
    current_datetime = timezone.now()
    
    # Initialize form data and errors
    form_data = {}
    form_errors = {}
    form_type = None
    
    # Get reports based on role
    if is_admin:
        # Admins and superadmins see all reports except drafts
        reports_queryset = Report.objects.exclude(status='draft')
        teachers = User.objects.filter(groups__name='teacher_group')
    elif is_teacher:
        # Teachers see reports assigned to them
        reports_queryset = Report.objects.filter(assigned_to=user)
        teachers = None
    else:
        # Students see only their own reports
        reports_queryset = Report.objects.filter(student=user)
        teachers = None
    
    # Apply filters
    if filter_status and filter_status != 'all':
        reports_queryset = reports_queryset.filter(status=filter_status)
    
    # Apply search query
    if search_query:
        transliterated_query = translit(search_query, 'ru', reversed=True)  
        
        if search_field == 'title':
            reports_queryset = reports_queryset.filter(
                Q(title__icontains=search_query) |
                Q(title__icontains=transliterated_query)
            )
        elif search_field == 'description':
            reports_queryset = reports_queryset.filter(
                Q(description__icontains=search_query) |
                Q(description__icontains=transliterated_query)
            )
        elif search_field == 'type':
            reports_queryset = reports_queryset.filter(
                Q(report_type__icontains=search_query) |
                Q(report_type__icontains=transliterated_query)
            )
        elif search_field == 'student_name':
            # Search by student's full name in profile
            reports_queryset = reports_queryset.filter(
                Q(student__profile__full_name__icontains=search_query) |
                Q(student__profile__full_name__icontains=transliterated_query)
            )
        else:  # search all fields
            reports_queryset = reports_queryset.filter(
                Q(title__icontains=search_query) | Q(title__icontains=transliterated_query) |
                Q(description__icontains=search_query) | Q(description__icontains=transliterated_query) | 
                Q(report_type__icontains=search_query) | Q(report_type__icontains=transliterated_query) |
                Q(student__profile__full_name__icontains=search_query) | Q(student__profile__full_name__icontains=transliterated_query)
            )
    
    # Order by most recent first
    reports_queryset = reports_queryset.order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    items_per_page = 5  # You can adjust this number
    paginator = Paginator(reports_queryset, items_per_page)
    
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        reports = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        reports = paginator.page(paginator.num_pages)
    
    # Create a custom page range for pagination links
    # Show first page, last page, and a few pages around the current page
    paginator_range = []
    current_page = reports.number
    total_pages = paginator.num_pages
    
    # Always include first page
    paginator_range.append(1)
    
    # Add pages around current page
    for i in range(max(2, current_page - 2), min(current_page + 3, total_pages + 1)):
        if i == 2 and current_page - 2 > 2:
            paginator_range.append('...')
        paginator_range.append(i)
    
    # Add last page
    if total_pages > 1 and total_pages not in paginator_range:
        if current_page + 3 < total_pages:
            paginator_range.append('...')
        paginator_range.append(total_pages)
    
    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')
        form_type = action  # Set form_type for template rendering
        
        # Add new report (student) - can be saved as draft or submitted
        if action == 'add_report' and is_student:
            if is_admin:
                messages.error(request, _('you_do_not_have_permission_to_add'))
                return redirect('report')
            
            ReportForm = modelform_factory(
                Report, 
                fields=['title', 'description', 'report_type', 'file']
            )
            form = ReportForm(request.POST, request.FILES)
            # Store form data for redisplay on error
            form_data = request.POST.dict()
            
            # Validate file separately if present
            if 'file' in request.FILES:
                file_valid, file_error = validate_report_file(request.FILES['file'])
                if not file_valid:
                    if form.is_valid():  # Initial validation passed, but file validation failed
                        form_errors = {'file': [file_error]}
                        messages.error(request, file_error)
                    else:
                        form_errors = form.errors
                        form_errors['file'] = [file_error]
                    messages.error(request, _('please_fix_the_errors_in_the_form'))
                    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'), {
                        'reports': reports,
                        'is_student': is_student,
                        'is_teacher': is_teacher, 
                        'is_admin': is_admin,
                        'teachers': teachers,
                        'paginator_range': paginator_range,
                        'filter_status': filter_status,
                        'search_query': search_query,
                        'search_field': search_field,
                        'current_date': current_datetime,
                        'form_errors': form_errors,
                        'form_data': form_data,
                        'form_type': 'add_report',
                    })
            
            if form.is_valid():
                report = form.save(commit=False)
                report.student = user
                
                # Set status based on submit button (draft or submit)
                submit_type = request.POST.get('submit_type', 'submit')
                if submit_type == 'draft':
                    report.status = 'draft'
                else:
                    report.status = 'submitted'
                    report.submitted_at = timezone.now()
                
                # Due date can only be set by admins when assigning
                report.save()
                
                if submit_type == 'draft':
                    messages.success(request, _('report_saved_as_draft'))
                else:
                    messages.success(request, _('report_submitted_successfully'))
                return redirect('report')
            else:
                # Store validation errors for template display
                form_errors = form.errors
                messages.error(request, _('please_fix_the_errors_in_the_form'))
        
        # Update existing report (student only)
        elif action == 'update_report' and is_student:
            if is_admin:
                messages.error(request, _('you_do_not_have_permission_to_update'))
                return redirect('report')
            
            report_id = request.POST.get('report_id')
            report = get_object_or_404(Report, id=report_id, student=user)
            form_data = request.POST.dict()
            
            # Only allow updates if report is in draft or submitted state
            if report.status in ['draft', 'submitted']:
                ReportForm = modelform_factory(
                    Report, 
                    fields=['title', 'description', 'report_type', 'file']
                )
                
                # Validate file separately if present
                if 'file' in request.FILES:
                    file_valid, file_error = validate_report_file(request.FILES['file'])
                    if not file_valid:
                        form = ReportForm(request.POST, instance=report)
                        if form.is_valid():  # Initial validation passed, but file validation failed
                            form_errors = {'file': [file_error]}
                            messages.error(request, file_error)
                        else:
                            form_errors = form.errors
                            form_errors['file'] = [file_error]
                        messages.error(request, _('please_fix_the_errors_in_the_form'))
                        return render(request, os.path.join(TEMPLATE_DIR, 'index.html'), {
                            'reports': reports,
                            'is_student': is_student,
                            'is_teacher': is_teacher, 
                            'is_admin': is_admin,
                            'teachers': teachers,
                            'paginator_range': paginator_range,
                            'filter_status': filter_status,
                            'search_query': search_query,
                            'search_field': search_field,
                            'current_date': current_datetime,
                            'form_errors': form_errors,
                            'form_data': form_data,
                            'form_type': 'update_report',
                        })
                
                form = ReportForm(request.POST, request.FILES, instance=report)
                if form.is_valid():
                    updated_report = form.save(commit=False)
                    
                    # Set status based on submit button (draft or submit)
                    submit_type = request.POST.get('submit_type', 'submit')
                    if submit_type == 'draft':
                        updated_report.status = 'draft'
                    else:
                        updated_report.status = 'submitted'
                        updated_report.submitted_at = timezone.now()
                    
                    updated_report.save()
                    
                    if submit_type == 'draft':
                        messages.success(request, _('report_saved_as_draft'))
                    else:
                        messages.success(request, _('report_updated_and_submitted_successfully'))
                    return redirect('report')
                else:
                    # Store validation errors for template display
                    form_errors = form.errors
                    messages.error(request, _('please_fix_the_errors_in_the_form'))
            else:
                messages.error(request, _('you_can_only_update_reports_in_draft_or_submitted_status'))
        
        # Approve report (teacher) - only before due date
        elif action == 'approve_report' and is_teacher:
            report_id = request.POST.get('report_id')
            feedback = request.POST.get('feedback')
            report = get_object_or_404(Report, id=report_id, assigned_to=user)
            form_data = {'feedback': feedback, 'report_id': report_id}
            
            # Check if the report is past due date
            if report.due_date and current_datetime > report.due_date:
                messages.error(request, _('cannot_approve_report_past_due_date'))
                return redirect('report')
            
            # Validate feedback (optional for approval)
            if report.status == 'submitted' or report.status == 'pending':
                # Simple validation - no form class needed for this case
                report.status = 'approved'
                report.feedback = feedback
                report.reviewed_by = user
                report.review_date = current_datetime
                report.save()
                messages.success(request, _('report_approved_successfully'))
                return redirect('report')
        
        # Reject report (teacher) - only before due date
        elif action == 'reject_report' and is_teacher:
            report_id = request.POST.get('report_id')
            feedback = request.POST.get('feedback')
            report = get_object_or_404(Report, id=report_id, assigned_to=user)
            form_data = {'feedback': feedback, 'report_id': report_id}
            
            # Check if the report is past due date
            if report.due_date and current_datetime > report.due_date:
                messages.error(request, _('cannot_reject_report_past_due_date'))
                return redirect('report')
            
            # Validate feedback (required for rejection)
            if report.status == 'submitted' or report.status == 'pending':
                if not feedback or feedback.strip() == '':
                    form_errors = {'feedback': [_('feedback_is_required_when_rejecting_a_report')]}
                    messages.error(request, _('please_provide_feedback_when_rejecting_a_report'))
                else:
                    report.status = 'rejected'
                    report.feedback = feedback
                    report.reviewed_by = user
                    report.review_date = current_datetime
                    report.save()
                    messages.success(request, _('report_rejected_successfully'))
                    return redirect('report')
        
        # Assign report to teacher (admin) - including setting due date
        elif action == 'assign_report' and is_admin:
            report_id = request.POST.get('report_id')
            teacher_id = request.POST.get('teacher_id')
            due_date = request.POST.get('due_date')
            form_data = {'teacher_id': teacher_id, 'due_date': due_date, 'report_id': report_id}
            
            report = get_object_or_404(Report, id=report_id)
            
            # Validate required fields
            form_errors = {}
            if not teacher_id:
                form_errors['teacher_id'] = [_('teacher_selection_is_required')]
            if not due_date:
                form_errors['due_date'] = [_('due_date_is_required')]
                
            if not form_errors:
                try:
                    teacher = User.objects.get(id=teacher_id)
                    # Check if the assigned user is actually a teacher
                    if Group.objects.get(name='teacher_group') in teacher.groups.all():
                        report.assigned_to = teacher
                        
                        # Set due date when assigning
                        if due_date:
                            report.due_date = due_date
                        
                        # Change status to pending when assigned to a teacher
                        if report.status == 'submitted' or report.status == 'draft':
                            report.status = 'pending'
                        report.save()
                        messages.success(request, _('report_assigned_successfully_with_due_date'))
                        return redirect('report')
                    else:
                        form_errors['teacher_id'] = [_('selected_user_is_not_a_teacher')]
                        messages.error(request, _('selected_user_is_not_a_teacher'))
                except User.DoesNotExist:
                    form_errors['teacher_id'] = [_('selected_teacher_does_not_exist')]
                    messages.error(request, _('selected_teacher_does_not_exist'))
            else:
                messages.error(request, _('please_fix_the_errors_in_the_form'))
        
        # Delete report (admin or student who owns the report)
        elif action == 'delete_report':
            report_id = request.POST.get('report_id')
            
            if is_admin:
                report = get_object_or_404(Report, id=report_id)
            elif is_student:
                report = get_object_or_404(Report, id=report_id, student=user)
            else:
                return HttpResponseForbidden(_("you_dont_have_permission_to_delete_this_report"))
            
            report.delete()
            messages.success(request, _('report_deleted_successfully'))
            
            # Preserve filter and search parameters when redirecting
            redirect_url = reverse('report')
            params = []
            if filter_status:
                params.append(f'status={filter_status}')
            if search_query:
                params.append(f'search={search_query}')
            if search_field:
                params.append(f'search_field={search_field}')
            if page and page != '1':
                params.append(f'page={page}')
            
            if params:
                redirect_url += '?' + '&'.join(params)
            
            return redirect(redirect_url)
    
    context = {
        'reports': reports,
        'is_student': is_student,
        'is_teacher': is_teacher, 
        'is_admin': is_admin,
        'teachers': teachers,
        'paginator_range': paginator_range,
        'filter_status': filter_status,
        'search_query': search_query,
        'search_field': search_field,
        'current_date': current_datetime,
        'form_errors': form_errors,
        'form_data': form_data,
        'form_type': form_type,
    }
    
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'), context)


def auto_approve_reports(is_admin_request=False):
    """Auto approve reports that are past their due date and still pending/submitted"""
    current_datetime = timezone.now()
    
    # Find reports past due date that are not yet approved/rejected
    reports_to_approve = Report.objects.filter(
        Q(status='pending') | Q(status='submitted'),
        due_date__lt=current_datetime,
        assigned_to__isnull=False
    )
    
    for report in reports_to_approve:
        report.status = 'approved'
        report.feedback = _("teacher_did_not_review_by_due_date_automatically_approved")
        report.review_date = current_datetime
        report.save()
    
    # If called from an admin request, show a message about auto-approved reports
    if is_admin_request and reports_to_approve.count() > 0:
        return reports_to_approve.count()
    
    return 0
