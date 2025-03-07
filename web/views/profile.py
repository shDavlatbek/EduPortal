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
    
    # Form handling
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # Save the active tab for redirecting back to the same tab
        if request.POST.get('active_tab'):
            active_tab = request.POST.get('active_tab')
        
        # Handle profile form
        if form_type == 'profile':
            ProfileForm = modelform_factory(
                Profile, 
                fields=['full_name', 'picture', 'birth_date', 'gender', 
                       'birth_place', 'living_place', 'passport_number']
            )
            form = ProfileForm(request.POST, request.FILES, instance=profile_instance)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully')
                return redirect(f"{reverse('profile')}?tab={active_tab}")
        
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
                messages.success(request, 'Education profile updated successfully')
                return redirect(f"{reverse('profile')}?tab={active_tab}")
            
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
                messages.success(request, 'Certificate added successfully')
                return redirect(f"{reverse('profile')}?tab={active_tab}")
                
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
                messages.success(request, 'Article added successfully')
                return redirect(f"{reverse('profile')}?tab={active_tab}")
        
        # Handle dissertation form
        elif form_type == 'dissertation':
            DissertationForm = modelform_factory(
                Dissertation,
                fields=['dissertation_title', 'dissertation_progress', 'dissertation_file']
            )
            form = DissertationForm(request.POST, request.FILES, instance=dissertation)
            if form.is_valid():
                form.save()
                messages.success(request, 'Dissertation updated successfully')
                return redirect(f"{reverse('profile')}?tab={active_tab}")
        
        # Handle password change form
        elif form_type == 'password':
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                # Update the session to prevent the user from being logged out
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect(f"{reverse('profile')}?tab={active_tab}")
            else:
                # If form is invalid, we'll display the errors in the template
                active_tab = 'password'
                
        # Handle certificate deletion
        elif form_type == 'certificate_delete':
            certificate_id = request.POST.get('certificate_id')
            try:
                certificate = LanguageCertificate.objects.get(id=certificate_id, user=user)
                certificate.delete()
                messages.success(request, 'Certificate deleted successfully')
            except LanguageCertificate.DoesNotExist:
                messages.error(request, 'Certificate not found')
            return redirect(f"{reverse('profile')}?tab={active_tab}")
            
        # Handle article deletion
        elif form_type == 'article_delete':
            article_id = request.POST.get('article_id')
            try:
                article = Article.objects.get(id=article_id, user=user)
                article.delete()
                messages.success(request, 'Article deleted successfully')
            except Article.DoesNotExist:
                messages.error(request, 'Article not found')
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
    }
    
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'), context)
