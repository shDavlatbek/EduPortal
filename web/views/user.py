from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from web.models import ARTICLE_TYPES, EDUCATION_CHOICES, User, Profile, EducationProfile, Report, NextEducationMajor, LanguageCertificate, Article
from django.contrib.auth.models import Group
import os
from datetime import datetime
from django.urls import reverse
from django.http import HttpResponse
import xlsxwriter
from io import BytesIO

TEMPLATE_PATH = "user"

def is_admin(user):
    """Check if user is in admin_group or is superadmin"""
    return user.groups.filter(name__in=['admin_group', 'superadmin_group']).exists() or user.is_superuser

@login_required
@user_passes_test(is_admin)
def user(request):
    """
    View for listing student users and single student details
    """
    # Handle form submissions
    if request.method == 'POST':
        if 'form_type' in request.POST and 'student_id' in request.POST:
            form_type = request.POST.get('form_type')
            student_id = request.POST.get('student_id')
            
            # Get the student
            try:
                student = User.objects.get(id=student_id, groups__name='student_group')
                
                # Handle different form types
                if form_type == 'password_reset':
                    return reset_password(request, student)
                elif form_type == 'certificate_add':
                    return add_certificate(request, student)
                elif form_type == 'certificate_delete':
                    return delete_certificate(request, student)
                elif form_type == 'article_add':
                    return add_article(request, student)
                elif form_type == 'article_delete':
                    return delete_article(request, student)
                elif form_type == 'student_delete':
                    return delete_student(request, student)
            except User.DoesNotExist:
                messages.error(request, _('Student not found'))
                return redirect('user')
        # Handle action="update" from the student edit form
        elif 'action' in request.POST and request.POST.get('action') == 'update':
            return update_student(request)
    
    # Check if we're viewing a single student
    student_id = request.GET.get('student_id')
    
    if student_id:
        # Single student view
        try:
            student_detail = User.objects.get(username=student_id, groups__name='student_group')
            edit_mode = request.GET.get('edit', False) == 'true'
            
            # Get choices for the edit form
            from web.models import EDUCATION_CHOICES, ARTICLE_TYPES
            education_choices = EDUCATION_CHOICES
            education_majors = NextEducationMajor.objects.all().order_by('number')
            article_types = ARTICLE_TYPES
            
            context = {
                'student_detail': student_detail,
                'edit_mode': edit_mode,
                'education_choices': education_choices,
                'education_majors': education_majors,
                'article_types': article_types,
            }
            
            return render(request, os.path.join(TEMPLATE_PATH, "index.html"), context)
            
        except User.DoesNotExist:
            messages.error(request, _('Student not found'))
            return redirect('user')
    
    # Multiple students view (list)
    # Get all students
    students_query = User.objects.filter(groups__name='student_group')
    
    # Get filter parameters
    filter_education_type = request.GET.get('education_type', '')
    filter_education_level = request.GET.get('education_level', '')
    filter_education_major = request.GET.get('education_major', '')
    filter_gender = request.GET.get('gender', '')
    filter_status = request.GET.get('status', '')
    filter_reports_count = request.GET.get('reports_count', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    is_filtered = False
    filter_count = 0
    
    # Education type filter
    if filter_education_type:
        students_query = students_query.filter(edu_profile__next_education=filter_education_type)
        is_filtered = True
        filter_count += 1
    
    # Education level filter
    if filter_education_level:
        students_query = students_query.filter(edu_profile__next_education_level=filter_education_level)
        is_filtered = True
        filter_count += 1
    
    # Education major filter
    if filter_education_major:
        students_query = students_query.filter(edu_profile__next_education_major_id=filter_education_major)
        is_filtered = True
        filter_count += 1
    
    # Gender filter
    if filter_gender:
        students_query = students_query.filter(profile__gender=filter_gender)
        is_filtered = True
        filter_count += 1
    
    # Status filter
    if filter_status:
        is_active = (filter_status == 'active')
        students_query = students_query.filter(is_active=is_active)
        is_filtered = True
        filter_count += 1
    
    # Search functionality
    if search_query:
        students_query = students_query.filter(
            Q(profile__full_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(edu_profile__next_education_major__number__icontains=search_query) |
            Q(edu_profile__next_education_major__name__icontains=search_query)
        )
    
    # Annotate with report count
    students_query = students_query.annotate(report_count=Count('student_reports'))
    
    # Reports count filter
    if filter_reports_count:
        if filter_reports_count == '0':
            students_query = students_query.filter(report_count=0)
        elif filter_reports_count == '1-5':
            students_query = students_query.filter(report_count__gte=1, report_count__lte=5)
        elif filter_reports_count == '6-10':
            students_query = students_query.filter(report_count__gte=6, report_count__lte=10)
        elif filter_reports_count == '10+':
            students_query = students_query.filter(report_count__gt=10)
        is_filtered = True
        filter_count += 1
    
    # Pagination
    paginator = Paginator(students_query, 12)  # Show 12 students per page
    page = request.GET.get('page')
    
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        students = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        students = paginator.page(paginator.num_pages)
    
    # Get choices for the new user form and filters
    from web.models import EDUCATION_CHOICES
    education_choices = EDUCATION_CHOICES
    education_majors = NextEducationMajor.objects.all().order_by('number')
    
    context = {
        'students': students,
        'search_query': search_query,
        'education_choices': education_choices,
        'education_majors': education_majors,
        'is_filtered': is_filtered,
        'filter_count': filter_count,
        'filter_education_type': filter_education_type,
        'filter_education_level': filter_education_level,
        'filter_education_major': filter_education_major,
        'filter_gender': filter_gender,
        'filter_status': filter_status,
        'filter_reports_count': filter_reports_count,
    }
    
    return render(request, os.path.join(TEMPLATE_PATH, "index.html"), context)

def delete_student(request, student):
    """
    Delete a student
    """
    try:
        student.delete()
        messages.success(request, _('Student deleted successfully'))
    except Exception as e:
        messages.error(request, _('Error deleting student: ') + str(e))
    
    return redirect(reverse('user'))

def update_student(request):
    """
    Update student profile and education info
    """
    student_id = request.POST.get('student_id')
    
    try:
        # Try to get the student by ID first
        try:
            student = User.objects.get(id=student_id, groups__name='student_group')
        except (User.DoesNotExist, ValueError):
            # If ID doesn't work, try username
            student = User.objects.get(username=student_id, groups__name='student_group')
        
        # Update profile
        profile = student.profile
        profile.full_name = request.POST.get('full_name')
        profile.birth_date = request.POST.get('birth_date') or None
        profile.gender = request.POST.get('gender')
        profile.birth_place = request.POST.get('birth_place')
        profile.living_place = request.POST.get('living_place')
        profile.passport_number = request.POST.get('passport_number')
        profile.phone_number = request.POST.get('phone_number')
        profile.email = request.POST.get('email')
        
        if 'picture' in request.FILES:
            profile.picture = request.FILES['picture']
            
        profile.save()
        
        # Update education profile
        edu_profile = student.edu_profile
        edu_profile.bachelor_major = request.POST.get('bachelor_major')
        edu_profile.bachelor_diploma = request.POST.get('bachelor_diploma')
        edu_profile.bachelor_diploma_date = request.POST.get('bachelor_diploma_date') or None
        edu_profile.master_major = request.POST.get('master_major')
        edu_profile.master_diploma = request.POST.get('master_diploma')
        edu_profile.master_diploma_date = request.POST.get('master_diploma_date') or None
        edu_profile.next_education = request.POST.get('next_education')
        edu_profile.next_education_level = request.POST.get('next_education_level')
        
        education_major_id = request.POST.get('next_education_major')
        if education_major_id:
            edu_profile.next_education_major_id = education_major_id
        else:
            edu_profile.next_education_major = None
            
        edu_profile.teacher_full_name = request.POST.get('teacher_full_name')
        edu_profile.teacher_degree = request.POST.get('teacher_degree')
        edu_profile.teacher_academic_rank = request.POST.get('teacher_academic_rank')
        edu_profile.teacher_work_place_position = request.POST.get('teacher_work_place_position')
        edu_profile.order_number = request.POST.get('order_number')
        edu_profile.order_date = request.POST.get('order_date') or None
        edu_profile.save()
        
        messages.success(request, _('Student updated successfully'))
    except Exception as e:
        messages.error(request, _('Error updating student: ') + str(e))
    
    return redirect(f"{reverse('user')}?student_id={student.username}")

def reset_password(request, student):
    """
    Reset student password
    """
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_new_password')
    
    if new_password != confirm_password:
        messages.error(request, _(f'Passwords do not match {new_password} {confirm_password}'))
        return redirect(f"{reverse('user')}?student_id={student.username}")
    
    try:
        student.set_password(new_password)
        student.save()
        messages.success(request, _('Password reset successfully'))
    except Exception as e:
        messages.error(request, _('Error resetting password: ') + str(e))
    
    return redirect(f"{reverse('user')}?student_id={student.username}")

def add_certificate(request, student):
    """
    Add a language certificate
    """
    certificate_name = request.POST.get('certificate_name')
    certificate_date = request.POST.get('certificate_date')
    certificate_file = request.FILES.get('certificate_file')
    
    if not certificate_name:
        messages.error(request, _('Certificate name is required'))
        return redirect(f"{reverse('user')}?student_id={student.username}")
    
    try:
        certificate = LanguageCertificate.objects.create(
            user=student,
            certificate_name=certificate_name,
            certificate_date=certificate_date if certificate_date else None,
            certificate_file=certificate_file if certificate_file else None
        )
        messages.success(request, _('Certificate added successfully'))
    except Exception as e:
        messages.error(request, _('Error adding certificate: ') + str(e))
    
    return redirect(f"{reverse('user')}?student_id={student.username}")

def delete_certificate(request, student):
    """
    Delete a language certificate
    """
    certificate_id = request.POST.get('certificate_id')
    
    try:
        certificate = LanguageCertificate.objects.get(id=certificate_id, user=student)
        certificate.delete()
        messages.success(request, _('Certificate deleted successfully'))
    except LanguageCertificate.DoesNotExist:
        messages.error(request, _('Certificate not found'))
    except Exception as e:
        messages.error(request, _('Error deleting certificate: ') + str(e))
    
    return redirect(f"{reverse('user')}?student_id={student.username}")

def add_article(request, student):
    """
    Add an article
    """
    article_type = request.POST.get('article_type')
    article_number = request.POST.get('article_number')
    article_date = request.POST.get('article_date')
    article_file = request.FILES.get('article_file')
    
    if not article_type:
        messages.error(request, _('Article type is required'))
        return redirect(f"{reverse('user')}?student_id={student.username}")
    
    try:
        article = Article.objects.create(
            user=student,
            article_type=article_type,
            article_number=article_number,
            article_date=article_date if article_date else None,
            article_file=article_file if article_file else None
        )
        messages.success(request, _('Article added successfully'))
    except Exception as e:
        messages.error(request, _('Error adding article: ') + str(e))
    
    return redirect(f"{reverse('user')}?student_id={student.username}")

def delete_article(request, student):
    """
    Delete an article
    """
    article_id = request.POST.get('article_id')
    
    try:
        article = Article.objects.get(id=article_id, user=student)
        article.delete()
        messages.success(request, _('Article deleted successfully'))
    except Article.DoesNotExist:
        messages.error(request, _('Article not found'))
    except Exception as e:
        messages.error(request, _('Error deleting article: ') + str(e))
    
    return redirect(f"{reverse('user')}?student_id={student.username}")

@login_required
@user_passes_test(is_admin)
def user_add(request):
    """
    View for adding a new student user
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name')
        next_education = request.POST.get('next_education')
        next_education_major_id = request.POST.get('next_education_major')
        
        # Validate form data
        if User.objects.filter(username=username).exists():
            messages.error(request, _('Username already exists'))
            return redirect('user')
            
        if password != confirm_password:
            messages.error(request, _('Passwords do not match'))
            return redirect('user')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Add to student group
            student_group = Group.objects.get(name='student_group')
            user.groups.add(student_group)
            
            # Create profile
            profile = Profile.objects.create(
                user=user,
                full_name=full_name,
                email=email
            )
            
            # Create education profile
            edu_profile = EducationProfile.objects.create(
                user=user,
                next_education=next_education if next_education else None
            )
            
            # Set education major if provided
            if next_education_major_id:
                try:
                    next_education_major = NextEducationMajor.objects.get(id=next_education_major_id)
                    edu_profile.next_education_major = next_education_major
                    edu_profile.save()
                except NextEducationMajor.DoesNotExist:
                    pass
            
            messages.success(request, _('Student successfully added'))
            # Redirect to the newly created student's page
            return redirect(f'user?student_id={user.username}')
        except Exception as e:
            messages.error(request, _('Error adding student: ') + str(e))
        
        return redirect('user')
    
    # If not POST, redirect to user list
    return redirect('user')

@login_required
@user_passes_test(is_admin)
def export_students(request):
    """
    Export students to Excel file with selected fields
    """
    # Get filter parameters from the request
    search_query = request.GET.get('search', '')
    filter_education_type = request.GET.get('education_type', '')
    filter_education_level = request.GET.get('education_level', '')
    filter_education_major = request.GET.get('education_major', '')
    filter_gender = request.GET.get('gender', '')
    filter_reports_count = request.GET.get('reports_count', '')
    
    # Get include options
    include_personal = request.GET.get('include_personal') == '1'
    include_education = request.GET.get('include_education') == '1'
    include_certificates = request.GET.get('include_certificates') == '1'
    include_articles = request.GET.get('include_articles') == '1'
    
    # Get selected fields
    selected_fields = request.GET.getlist('fields')
    
    # Filter students
    students = User.objects.filter(groups__name='student_group').select_related('profile', 'edu_profile')
    
    # Apply search query if provided
    if search_query:
        students = students.filter(
            Q(profile__full_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(edu_profile__next_education_major__name__icontains=search_query)
        )
    
    # Apply other filters
    if filter_education_type:
        students = students.filter(edu_profile__next_education=filter_education_type)
    
    if filter_education_level:
        students = students.filter(edu_profile__next_education_level=filter_education_level)
    
    if filter_education_major:
        students = students.filter(edu_profile__next_education_major_id=filter_education_major)
    
    if filter_gender:
        students = students.filter(profile__gender=filter_gender)
    
    # Reports count filtering
    if filter_reports_count:
        if filter_reports_count == '0':
            students = students.annotate(reports_count=Count('student_reports')).filter(reports_count=0)
        elif filter_reports_count == '1-5':
            students = students.annotate(reports_count=Count('student_reports')).filter(reports_count__gte=1, reports_count__lte=5)
        elif filter_reports_count == '6-10':
            students = students.annotate(reports_count=Count('student_reports')).filter(reports_count__gte=6, reports_count__lte=10)
        elif filter_reports_count == '10+':
            students = students.annotate(reports_count=Count('student_reports')).filter(reports_count__gt=10)
    
    # Create Excel file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    # Add formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4e73df',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
    })
    
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
    })
    
    # Create main worksheet
    worksheet = workbook.add_worksheet(str(_('Students')))
    worksheet.set_column('A:Z', 20)  # Set column width
    
    # Initialize column index
    col_idx = 0
    headers = []
    fields_mapping = {}
    
    # Add username as the first column always
    headers.append(str(_('username')))
    fields_mapping[col_idx] = 'username'
    col_idx += 1
    
    # Setup personal information columns
    if include_personal:
        personal_fields = {
            'full_name': str(_('full_name')),
            'gender': str(_('gender')),
            'birth_date': str(_('birth_date')),
            'email': str(_('email')),
            'phone_number': str(_('phone_number')),
            'birth_place': str(_('birth_place')),
            'living_place': str(_('living_place')),
            'passport_number': str(_('passport_number')),
        }
        
        for field in selected_fields:
            if field in personal_fields:
                headers.append(personal_fields[field])
                fields_mapping[col_idx] = f'profile__{field}'
                col_idx += 1
    
    # Setup education columns
    if include_education:
        education_fields = {
            'next_education': str(_('education_type')),
            'next_education_level': str(_('education_level')),
            'next_education_major': str(_('education_major')),
            'bachelor_major': str(_('bachelor_major')),
            'bachelor_diploma': str(_('bachelor_diploma')),
            'master_major': str(_('master_major')),
            'master_diploma': str(_('master_diploma')),
            'teacher_full_name': str(_('teacher_full_name')),
            'teacher_degree': str(_('teacher_degree')),
        }
        
        for field in selected_fields:
            if field in education_fields:
                headers.append(education_fields[field])
                if field == 'next_education_major':
                    fields_mapping[col_idx] = 'edu_profile__next_education_major__name'
                else:
                    fields_mapping[col_idx] = f'edu_profile__{field}'
                col_idx += 1
    
    # Write headers
    for i, header in enumerate(headers):
        worksheet.write(0, i, header, header_format)
    
    # Write data
    for row_idx, student in enumerate(students, start=1):
        for col_idx, field in fields_mapping.items():
            if field == 'username':
                worksheet.write(row_idx, col_idx, student.username, cell_format)
            elif field.startswith('profile__'):
                attr = field.replace('profile__', '')
                value = getattr(student.profile, attr, '')
                if attr == 'gender' and value:
                    value = str(_('male')) if value == 'male' else str(_('female'))
                elif attr == 'birth_date' and value:
                    value = value.strftime('%Y-%m-%d')
                worksheet.write(row_idx, col_idx, str(value) if value else '', cell_format)
            elif field.startswith('edu_profile__'):
                if field == 'edu_profile__next_education_major__name':
                    major = student.edu_profile.next_education_major
                    value = major.name if major else ''
                else:
                    attr = field.replace('edu_profile__', '')
                    value = getattr(student.edu_profile, attr, '')
                    # Format education type
                    if attr == 'next_education' and value:
                        for choice in EDUCATION_CHOICES:
                            if choice[0] == value:
                                value = str(choice[1])
                                break
                worksheet.write(row_idx, col_idx, str(value) if value else '', cell_format)
    
    # Add certificates sheet if requested
    if include_certificates:
        cert_sheet = workbook.add_worksheet(str(_('Certificates')))
        cert_sheet.set_column('A:Z', 20)
        
        # Write certificate headers
        cert_headers = [str(_('username')), str(_('full_name')), str(_('certificate_name')), str(_('certificate_date'))]
        for i, header in enumerate(cert_headers):
            cert_sheet.write(0, i, header, header_format)
        
        # Write certificate data
        row_idx = 1
        for student in students:
            certificates = student.language_certificates.all()
            if certificates.exists():
                for cert in certificates:
                    cert_sheet.write(row_idx, 0, student.username, cell_format)
                    cert_sheet.write(row_idx, 1, str(student.profile.full_name or ''), cell_format)
                    cert_sheet.write(row_idx, 2, str(cert.certificate_name), cell_format)
                    if cert.certificate_date:
                        cert_sheet.write(row_idx, 3, cert.certificate_date.strftime('%Y-%m-%d'), cell_format)
                    else:
                        cert_sheet.write(row_idx, 3, '', cell_format)
                    row_idx += 1
    
    # Add articles sheet if requested
    if include_articles:
        article_sheet = workbook.add_worksheet(str(_('Articles')))
        article_sheet.set_column('A:Z', 20)
        
        # Write article headers
        article_headers = [str(_('username')), str(_('full_name')), str(_('article_type')), str(_('article_number')), str(_('article_date'))]
        for i, header in enumerate(article_headers):
            article_sheet.write(0, i, header, header_format)
        
        # Write article data
        row_idx = 1
        for student in students:
            articles = student.articles.all()
            if articles.exists():
                for article in articles:
                    article_sheet.write(row_idx, 0, student.username, cell_format)
                    article_sheet.write(row_idx, 1, str(student.profile.full_name or ''), cell_format)
                    
                    # Translate article type
                    article_type = article.article_type
                    for choice in ARTICLE_TYPES:
                        if choice[0] == article_type:
                            article_type = str(choice[1])
                            break
                    
                    article_sheet.write(row_idx, 2, article_type, cell_format)
                    article_sheet.write(row_idx, 3, str(article.article_number or ''), cell_format)
                    if article.article_date:
                        article_sheet.write(row_idx, 4, article.article_date.strftime('%Y-%m-%d'), cell_format)
                    else:
                        article_sheet.write(row_idx, 4, '', cell_format)
                    row_idx += 1
    
    # Close the workbook
    workbook.close()
    
    # Create response
    output.seek(0)
    current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'students_export_{current_datetime}.xlsx'
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

