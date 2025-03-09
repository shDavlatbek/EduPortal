import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from web.models import Profile, EducationProfile, Article, LanguageCertificate, NextEducationMajor, Dissertation
from django.forms import modelform_factory
from django.utils.translation import gettext as _
TEMPLATE_DIR = 'profile'

@login_required
def profile(request):
    user = request.user
    
    # Get user's profile data
    profile_instance, created = Profile.objects.get_or_create(user=user)
    
    # Get education profile data
    education_profile, created = EducationProfile.objects.get_or_create(user=user)
    
    # Get language certificates
    language_certificates = LanguageCertificate.objects.filter(user=user)
    
    # Get articles
    articles = Article.objects.filter(user=user)
    
    # Get dissertation data
    dissertation, created = Dissertation.objects.get_or_create(user=user)
    
    # Get available education majors for dropdown
    education_majors = NextEducationMajor.objects.all()
    
    # Default active tab
    active_tab = request.GET.get('tab', 'personal')
    
    # Initialize password form
    password_form = PasswordChangeForm(user=user)
    
    # Initialize form errors and data
    form_errors = {}
    form_data = {}
    
    # Form handling
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # Save the active tab for redirecting back to the same tab
        if request.POST.get('active_tab'):
            active_tab = request.POST.get('active_tab')
        
        # Store form data for re-populating forms in case of errors
        form_data = request.POST.dict()
        
        # Handle profile form
        if form_type == 'profile':
            ProfileForm = modelform_factory(
                Profile, 
                fields=['full_name', 'picture', 'birth_date', 'gender', 
                       'birth_place', 'living_place', 'passport_number',
                       'phone_number', 'email']
            )
            form = ProfileForm(request.POST, request.FILES, instance=profile_instance)
            if form.is_valid():
                form.save()
                messages.success(request, _('profile_updated_successfully'))
                return redirect(f"{reverse('profile')}?tab={active_tab}")
            else:
                form_errors = form.errors
                messages.error(request, _('please_fix_the_errors_in_the_form'))
        
        # Handle education profile form
        elif form_type == 'education':
            EducationForm = modelform_factory(
                EducationProfile,
                fields=[
                    'bachelor_major', 'bachelor_diploma', 'bachelor_diploma_date',
                    'master_major', 'master_diploma', 'master_diploma_date',
                    'next_education', 'next_education_level', 'next_education_major',
                    'teacher_full_name', 'teacher_degree', 'teacher_academic_rank',
                    'teacher_work_place_position', 'order_number', 'order_date'
                ]
            )
            form = EducationForm(request.POST, instance=education_profile)
            if form.is_valid():
                form.save()
                messages.success(request, _('education_profile_updated_successfully'))
                return redirect(f"{reverse('profile')}?tab={active_tab}")
            else:
                form_errors = form.errors
                messages.error(request, _('please_fix_the_errors_in_the_form'))
            
        # Handle language certificate form
        elif form_type == 'certificate_add':
            CertificateForm = modelform_factory(
                LanguageCertificate,
                fields=['certificate_name', 'certificate_date', 'certificate_file']
            )
            form = CertificateForm(request.POST, request.FILES)
            if form.is_valid():
                certificate = form.save(commit=False)
                certificate.user = user
                certificate.save()
                messages.success(request, _('certificate_added_successfully'))
                return redirect(f"{reverse('profile')}?tab={active_tab}")
            else:
                form_errors = form.errors
                messages.error(request, _('please_fix_the_errors_in_the_form'))
                
        # Handle article form
        elif form_type == 'article_add':
            ArticleForm = modelform_factory(
                Article,
                fields=['article_type', 'article_number', 'article_date', 'article_file']
            )
            form = ArticleForm(request.POST, request.FILES)
            if form.is_valid():
                article = form.save(commit=False)
                article.user = user
                article.save()
                messages.success(request, _('article_added_successfully'))
                return redirect(f"{reverse('profile')}?tab={active_tab}")
            else:
                form_errors = form.errors
                messages.error(request, _('please_fix_the_errors_in_the_form'))
        
        # Handle dissertation form
        elif form_type == 'dissertation':
            DissertationForm = modelform_factory(
                Dissertation,
                fields=['dissertation_title', 'dissertation_progress', 'dissertation_file']
            )
            form = DissertationForm(request.POST, request.FILES, instance=dissertation)
            if form.is_valid():
                form.save()
                messages.success(request, _('dissertation_updated_successfully'))
                return redirect(f"{reverse('profile')}?tab={active_tab}")
            else:
                form_errors = form.errors
                messages.error(request, _('please_fix_the_errors_in_the_form'))
        
        # Handle password change form
        elif form_type == 'password':
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                # Update the session to prevent the user from being logged out
                update_session_auth_hash(request, user)
                messages.success(request, _('your_password_was_successfully_updated'))
                return redirect(f"{reverse('profile')}?tab={active_tab}")
            else:
                # If form is invalid, we'll use the errors from the password form
                form_errors = password_form.errors
                messages.error(request, _('please_fix_the_errors_in_the_form'))
                active_tab = 'password'
                
        # Handle certificate deletion
        elif form_type == 'certificate_delete':
            certificate_id = request.POST.get('certificate_id')
            try:
                certificate = LanguageCertificate.objects.get(id=certificate_id, user=user)
                certificate.delete()
                messages.success(request, _('certificate_deleted_successfully'))
            except LanguageCertificate.DoesNotExist:
                messages.error(request, _('certificate_not_found'))
            return redirect(f"{reverse('profile')}?tab={active_tab}")
            
        # Handle article deletion
        elif form_type == 'article_delete':
            article_id = request.POST.get('article_id')
            try:
                article = Article.objects.get(id=article_id, user=user)
                article.delete()
                messages.success(request, _('article_deleted_successfully'))
            except Article.DoesNotExist:
                messages.error(request, _('article_not_found'))
            return redirect(f"{reverse('profile')}?tab={active_tab}")
    
    context = {
        'profile': profile_instance,
        'education_profile': education_profile,
        'language_certificates': language_certificates,
        'articles': articles,
        'education_majors': education_majors,
        'dissertation': dissertation,
        'active_tab': active_tab,
        'password_form': password_form,
        'role': request.user.groups.first().name,
        'form_errors': form_errors,
        'form_data': form_data,
    }
    
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'), context)
