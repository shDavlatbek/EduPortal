from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from web.models import User, Profile
from django.contrib.auth.models import Group
import os
from datetime import datetime
from django.urls import reverse
from django.http import HttpResponse
import xlsxwriter
from io import BytesIO

TEMPLATE_PATH = "teacher"

def is_admin(user):
    """Check if user is in admin_group or is superadmin"""
    return user.groups.filter(name__in=['admin_group', 'superadmin_group']).exists() or user.is_superuser

@login_required
@user_passes_test(is_admin)
def teacher(request):
    """
    View for listing teacher users and single teacher details
    """
    # Handle form submissions
    if request.method == 'POST' and 'form_type' in request.POST and 'teacher_id' in request.POST:
        form_type = request.POST.get('form_type')
        teacher_id = request.POST.get('teacher_id')
        
        # Get the teacher
        try:
            teacher = User.objects.get(id=teacher_id, groups__name='teacher_group')
            
            if form_type == 'teacher_delete':
                return delete_teacher(request, teacher)
            elif form_type == 'password_reset':
                return reset_password(request, teacher)
            
        except User.DoesNotExist:
            messages.error(request, _("teacher_not_found"))
    
    # Check if it's a detail view or list view
    teacher_id = request.GET.get('teacher_id')
    edit_mode = request.GET.get('edit') == 'true'
    
    # Initialize search and filter parameters
    search_query = request.GET.get('search', '')
    filter_gender = request.GET.get('gender', '')
    
    # If requesting a teacher detail
    if teacher_id:
        try:
            teacher_detail = User.objects.get(username=teacher_id, groups__name='teacher_group')
            
            # If it's a form submission for updating
            if request.method == 'POST' and request.POST.get('action') == 'update':
                return update_teacher(request)
                
            context = {
                'teacher_detail': teacher_detail,
                'edit_mode': edit_mode,
            }
            
            return render(request, os.path.join(TEMPLATE_PATH, "index.html"), context)
            
        except User.DoesNotExist:
            messages.error(request, _("teacher_not_found"))
            return redirect('teacher')
    
    # List view - get all teachers
    teachers_list = User.objects.filter(groups__name='teacher_group')
    
    # Apply search if provided
    if search_query:
        teachers_list = teachers_list.filter(
            Q(username__icontains=search_query) |
            Q(profile__full_name__icontains=search_query)
        ).distinct()
    
    # Apply filters
    if filter_gender:
        teachers_list = teachers_list.filter(profile__gender=filter_gender)
    
    # Check if any filters are applied
    is_filtered = bool(filter_gender)
    
    # Count active filters
    filter_count = sum(1 for x in [filter_gender] if x)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(teachers_list, 12)  # Show 12 teachers per page
    
    try:
        teachers = paginator.page(page)
    except PageNotAnInteger:
        teachers = paginator.page(1)
    except EmptyPage:
        teachers = paginator.page(paginator.num_pages)
    
    context = {
        'teachers': teachers,
        'search_query': search_query,
        'filter_gender': filter_gender,
        'is_filtered': is_filtered,
        'filter_count': filter_count,
    }
    
    return render(request, os.path.join(TEMPLATE_PATH, "index.html"), context)

def delete_teacher(request, teacher):
    """Delete a teacher"""
    try:
        username = teacher.username
        teacher.delete()
        messages.success(request, _("teacher_deleted_successfully").format(username=username))
    except Exception as e:
        messages.error(request, _("error_deleting_teacher").format(error=str(e)))
    
    return redirect('teacher')

def update_teacher(request):
    """Update teacher information"""
    teacher_id = request.POST.get('teacher_id')
    
    try:
        teacher = User.objects.get(id=teacher_id, groups__name='teacher_group')
        
        # Update profile information
        if not hasattr(teacher, 'profile'):
            profile = Profile(user=teacher)
            profile.save()
        else:
            profile = teacher.profile
        
        profile.full_name = request.POST.get('full_name', '')
        profile.email = request.POST.get('email', '')
        profile.phone_number = request.POST.get('phone_number', '')
        profile.birth_date = request.POST.get('birth_date') or None
        profile.gender = request.POST.get('gender', '')
        profile.birth_place = request.POST.get('birth_place', '')
        profile.living_place = request.POST.get('living_place', '')
        profile.passport_number = request.POST.get('passport_number', '')
        
        # Handle profile picture if uploaded
        if 'picture' in request.FILES:
            profile.picture = request.FILES['picture']
        
        profile.save()
        
        messages.success(request, _("teacher_updated_successfully"))
        
    except User.DoesNotExist:
        messages.error(request, _("teacher_not_found"))
    except Exception as e:
        messages.error(request, _("error_updating_teacher").format(error=str(e)))
    
    return redirect('teacher')

def reset_password(request, teacher):
    """Reset teacher's password"""
    new_password = request.POST.get('new_password')
    confirm_new_password = request.POST.get('confirm_new_password')
    
    if new_password and new_password == confirm_new_password:
        try:
            teacher.set_password(new_password)
            teacher.save()
            messages.success(request, _("password_reset_successfully"))
        except Exception as e:
            messages.error(request, _("error_resetting_password").format(error=str(e)))
    else:
        messages.error(request, _("passwords_do_not_match"))
    
    return redirect('teacher')

@login_required
@user_passes_test(is_admin)
def teacher_add(request):
    """Add a new teacher"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name', '')
        
        # Validate input
        if not username or not password:
            messages.error(request, _("username_and_password_required"))
            return redirect('teacher')
        
        if password != confirm_password:
            messages.error(request, _("passwords_do_not_match"))
            return redirect('teacher')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, _("username_already_exists"))
            return redirect('teacher')
        
        try:
            # Create user
            teacher = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Add teacher to teacher group
            teacher_group, created = Group.objects.get_or_create(name='teacher_group')
            teacher.groups.add(teacher_group)
            
            # Create profile
            profile = Profile(
                user=teacher,
                full_name=full_name,
                email=email
            )
            profile.save()
            
            messages.success(request, _("teacher_added_successfully"))
            
            # Redirect to the newly created teacher detail page
            return redirect(f"{reverse('teacher')}?teacher_id={username}")
            
        except Exception as e:
            messages.error(request, _("error_adding_teacher").format(error=str(e)))
            return redirect('teacher')
    
    # If not POST, redirect to teacher list
    return redirect('teacher')

@login_required
@user_passes_test(is_admin)
def export_teachers(request):
    """Export teachers to Excel"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    filter_gender = request.GET.get('gender', '')
    
    # Get fields to include
    fields = request.GET.getlist('fields', [])
    include_personal = request.GET.get('include_personal') == '1'
    
    # Get teachers based on current filters
    teachers = User.objects.filter(groups__name='teacher_group')
    
    # Apply search if provided
    if search_query:
        teachers = teachers.filter(
            Q(username__icontains=search_query) |
            Q(profile__full_name__icontains=search_query)
        ).distinct()
    
    # Apply filters
    if filter_gender:
        teachers = teachers.filter(profile__gender=filter_gender)
    
    # Create Excel file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    
    # Create worksheet for teacher data
    worksheet = workbook.add_worksheet(str(_("Teachers")))
    
    # Define columns based on selected fields
    columns = []
    row = 0
    col = 0
    
    # Always include username
    columns.append({'header': str(_("username")), 'field': 'username'})
    
    # Add personal information columns
    if include_personal:
        if 'full_name' in fields:
            columns.append({'header': str(_("full_name")), 'field': 'profile__full_name'})
        if 'gender' in fields:
            columns.append({'header': str(_("gender")), 'field': 'profile__gender'})
        if 'birth_date' in fields:
            columns.append({'header': str(_("birth_date")), 'field': 'profile__birth_date'})
        if 'email' in fields:
            columns.append({'header': str(_("email")), 'field': 'profile__email'})
        if 'phone_number' in fields:
            columns.append({'header': str(_("phone_number")), 'field': 'profile__phone_number'})
        if 'birth_place' in fields:
            columns.append({'header': str(_("birth_place")), 'field': 'profile__birth_place'})
        if 'living_place' in fields:
            columns.append({'header': str(_("living_place")), 'field': 'profile__living_place'})
        if 'passport_number' in fields:
            columns.append({'header': str(_("passport_number")), 'field': 'profile__passport_number'})
    
    # Write headers
    for column in columns:
        worksheet.write(row, col, column['header'], header_format)
        col += 1
    
    # Write data
    row = 1
    for teacher in teachers:
        col = 0
        for column in columns:
            field = column['field']
            value = None
            
            # Get value based on field path
            if field == 'username':
                value = teacher.username
            elif field.startswith('profile__'):
                attr = field.replace('profile__', '')
                if hasattr(teacher, 'profile') and getattr(teacher.profile, attr, None) is not None:
                    value = getattr(teacher.profile, attr)
            
            # Format specific types
            if isinstance(value, datetime):
                worksheet.write_datetime(row, col, value, date_format)
            elif field == 'profile__gender' and value:
                worksheet.write(row, col, str(_(value)))
            else:
                worksheet.write(row, col, value if value is not None else '')
            
            col += 1
        
        row += 1
    
    # Adjust column widths
    for i, column in enumerate(columns):
        worksheet.set_column(i, i, 20)
    
    # Close the workbook
    workbook.close()
    
    # Create response
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=teachers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return response