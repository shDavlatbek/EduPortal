import os
from transliterate import translit
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext as _
from web.models import HelpRequest, User

TEMPLATE_DIR = 'help'

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

def validate_help_attachment(file):
    """
    Validates uploaded help attachment files
    
    Args:
        file: The uploaded file object
    
    Returns:
        A tuple (is_valid, error_message)
    """
    if not file:
        return True, None
        
    # Check if file is empty (0 bytes)
    if file.size == 0:
        return False, "uploaded_file_is_empty_upload_valid_file"
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        return False, "file_size_exceeds_limit_upload_smaller_file"
    
    # Check file extension
    _, ext = os.path.splitext(file.name)
    if ext.startswith('.'):
        ext = ext[1:]
    if ext.lower() not in ALLOWED_FILE_EXTENSIONS:
        formatted_extensions = ', '.join(['.' + ext for ext in ALLOWED_FILE_EXTENSIONS])
        return False, "this_file_type_is_not_allowed_extensions" + formatted_extensions
    
    return True, None

@login_required
def help(request):
    user = request.user
    user_groups = [g.name for g in user.groups.all()]
    
    # Determine user role
    is_student = 'student_group' in user_groups
    is_teacher = 'teacher_group' in user_groups
    is_admin = 'admin_group' in user_groups or 'superadmin_group' in user_groups
    
    form_errors = {}
    form_data = {}
    form_type = None
    
    # Process form submissions
    if request.method == 'POST':
        action = request.POST.get('action')
        form_type = action  # Set form_type for template rendering
        
        # Add new help request (all users)
        if action == 'add_help_request':
            if is_admin:
                messages.error(request, _("you_do_not_have_permission_to_add"))
                return redirect('help')
            
            form_data = request.POST.dict()
            
            # Validate attachment file if provided
            if 'attachment' in request.FILES:
                file_valid, file_error = validate_help_attachment(request.FILES.get('attachment'))
                if not file_valid:
                    form_errors = {'attachment': [file_error]}
                    messages.error(request, file_error)
                    form_type = 'add_help_request'
                else:
                    HelpRequestForm = modelform_factory(
                        HelpRequest, 
                        fields=['subject', 'message', 'request_type', 'attachment']
                    )
                    form = HelpRequestForm(request.POST, request.FILES)
                    
                    if form.is_valid():
                        help_request = form.save(commit=False)
                        help_request.user = user
                        help_request.status = 'open'
                        help_request.save()
                        
                        messages.success(request, _('help_request_submitted_successfully'))
                        return redirect('help')
                    else:
                        form_errors = form.errors
                        form_type = 'add_help_request'
                        messages.error(request, _('please_fix_the_errors_in_the_form'))
            else:
                # No file was submitted, just validate the form
                HelpRequestForm = modelform_factory(
                    HelpRequest, 
                    fields=['subject', 'message', 'request_type']
                )
                form = HelpRequestForm(request.POST)
                
                if form.is_valid():
                    help_request = form.save(commit=False)
                    help_request.user = user
                    help_request.status = 'open'
                    help_request.save()
                    
                    messages.success(request, _('help_request_submitted_successfully'))
                    return redirect('help')
                else:
                    form_errors = form.errors
                    form_type = 'add_help_request'
                    messages.error(request, _('please_fix_the_errors_in_the_form'))
        
        # Update existing help request (owner or admin)
        elif action == 'update_help_request':
            if is_admin:
                messages.error(request, _('you_do_not_have_permission_to_update'))
                return redirect('help')
            
            help_request_id = request.POST.get('help_request_id')
            
            try:
                # Check if user can edit this request
                help_request = HelpRequest.objects.get(id=help_request_id)
                if help_request.user != user and is_admin:
                    messages.error(request, _("you_cannot_edit_this_help_request"))
                    return redirect('help')
                
                form_data = request.POST.dict()
                
                # Only allow updates if help request is in open or in_progress state
                if help_request.status in ['open', 'in_progress']:
                    # Validate attachment file if provided
                    if 'attachment' in request.FILES:
                        file_valid, file_error = validate_help_attachment(request.FILES.get('attachment'))
                        if not file_valid:
                            form_errors = {'attachment': [file_error]}
                            messages.error(request, file_error)
                            form_type = 'update_help_request'
                        else:
                            HelpRequestForm = modelform_factory(
                                HelpRequest, 
                                fields=['subject', 'message', 'request_type', 'attachment']
                            )
                            form = HelpRequestForm(request.POST, request.FILES, instance=help_request)
                            
                            if form.is_valid():
                                help_request = form.save()
                                messages.success(request, _('help_request_updated_successfully'))
                                return redirect('help')
                            else:
                                form_errors = form.errors
                                form_type = 'update_help_request'
                                messages.error(request, _('please_fix_the_errors_in_the_form'))
                    else:
                        # No new file was submitted
                        HelpRequestForm = modelform_factory(
                            HelpRequest, 
                            fields=['subject', 'message', 'request_type']
                        )
                        form = HelpRequestForm(request.POST, instance=help_request)
                        
                        if form.is_valid():
                            help_request = form.save()
                            messages.success(request, _('help_request_updated_successfully'))
                            return redirect('help')
                        else:
                            form_errors = form.errors
                            form_type = 'update_help_request'
                            messages.error(request, _('please_fix_the_errors_in_the_form'))
                else:
                    messages.error(request, _('cannot_update_help_request_in_current_status'))
                    return redirect('help')
            except HelpRequest.DoesNotExist:
                messages.error(request, _('help_request_not_found'))
                return redirect('help')
        
        # Respond to help request (admin only)
        elif action == 'respond_to_help_request':
            if not is_admin:
                messages.error(request, _("you_do_not_have_permission_to_respond"))
                return redirect('help')
            
            help_request_id = request.POST.get('help_request_id')
            help_request = get_object_or_404(HelpRequest, id=help_request_id)
            
            response = request.POST.get('response')
            status = request.POST.get('status')
            form_data = {'response': response, 'status': status, 'help_request_id': help_request_id}
            
            if not response or response.strip() == '':
                form_errors = {'response': ['response_is_required']}
                form_type = 'respond_to_help_request'
                messages.error(request, _('response_is_required'))
            else:
                help_request.response = response
                help_request.status = status
                help_request.responded_by = user
                help_request.response_date = timezone.now()
                help_request.save()
                
                messages.success(request, _('response_sent_successfully'))
                return redirect('help')
        
        # Delete help request (owner or admin)
        elif action == 'delete_help_request':
            help_request_id = request.POST.get('help_request_id')
            
            try:
                # Check if user can delete this request
                help_request = HelpRequest.objects.get(id=help_request_id)
                if help_request.user != user and not is_admin:
                    messages.error(request, _("you_cannot_delete_this_help_request"))
                    return redirect('help')
                
                help_request.delete()
                messages.success(request, _('help_request_deleted_successfully'))
                
                # Preserve filter and search parameters when redirecting
                redirect_url = reverse('help')
                params = []
                if filter_status := request.GET.get('status'):
                    params.append(f'status={filter_status}')
                if search_query := request.GET.get('search'):
                    params.append(f'search={search_query}')
                if search_field := request.GET.get('search_field'):
                    params.append(f'search_field={search_field}')
                if page := request.GET.get('page'):
                    params.append(f'page={page}')
                
                if params:
                    redirect_url += '?' + '&'.join(params)
                
                return redirect(redirect_url)
            except HelpRequest.DoesNotExist:
                messages.error(request, _('help_request_not_found'))
                return redirect('help')
    
    # Filter help requests
    filter_status = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    search_field = request.GET.get('search_field', 'all')
    
    # Get help requests based on user's role
    if is_admin:
        # Admins see all help requests
        help_requests = HelpRequest.objects.all()
    else:
        # Regular users only see their own requests
        help_requests = HelpRequest.objects.filter(user=user)
    
    # Apply status filter
    if filter_status != 'all':
        help_requests = help_requests.filter(status=filter_status)
    
    # Apply search filter
    if search_query:
        transliterated_query = translit(search_query, 'ru', reversed=True)  # Convert Cyrillic ↔ Latin

        if search_field == 'subject':
            help_requests = help_requests.filter(
                Q(subject__icontains=search_query) | Q(subject__icontains=transliterated_query)
            )
        
        elif search_field == 'message':
            help_requests = help_requests.filter(
                Q(message__icontains=search_query) | Q(message__icontains=transliterated_query)
            )
        
        elif search_field == 'type':
            help_requests = help_requests.filter(
                Q(request_type__icontains=search_query) | Q(request_type__icontains=transliterated_query)
            )

        elif search_field == 'user_name' and is_admin:
            help_requests = help_requests.filter(
                Q(user__username__icontains=search_query) | 
                Q(user__profile__full_name__icontains=search_query) |
                Q(user__username__icontains=transliterated_query) | 
                Q(user__profile__full_name__icontains=transliterated_query)
            )

        else:  # 'all'
            help_requests = help_requests.filter(
                Q(subject__icontains=search_query) | Q(subject__icontains=transliterated_query) |
                Q(message__icontains=search_query) | Q(message__icontains=transliterated_query) |
                Q(request_type__icontains=search_query) | Q(request_type__icontains=transliterated_query) |
                Q(user__username__icontains=search_query) | Q(user__username__icontains=transliterated_query) |
                Q(user__profile__full_name__icontains=search_query) | Q(user__profile__full_name__icontains=transliterated_query)
            )
    
    # Sort by most recent first
    help_requests = help_requests.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(help_requests, 10)  # Show 10 help requests per page
    page = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        page_obj = paginator.page(paginator.num_pages)
    
    # Create pagination range for template
    paginator_range = []
    current_page = page_obj.number
    last_page = paginator.num_pages
    
    # Basic pagination algorithm to show current page and surroundings
    if last_page <= 7:
        paginator_range = range(1, last_page + 1)
    else:
        if current_page <= 4:
            paginator_range = list(range(1, 6)) + ['...', last_page]
        elif current_page >= last_page - 3:
            paginator_range = [1, '...'] + list(range(last_page - 4, last_page + 1))
        else:
            paginator_range = [1, '...'] + list(range(current_page - 1, current_page + 2)) + ['...', last_page]
    
    context = {
        'help_requests': page_obj,
        'filter_status': filter_status,
        'paginator_range': paginator_range,
        'search_query': search_query,
        'search_field': search_field,
        'is_admin': is_admin,
        'form_errors': form_errors,
        'form_data': form_data,
        'form_type': form_type,
    }
    
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'), context)
