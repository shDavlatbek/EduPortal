from django.contrib import admin
from .models import User, Profile, EducationProfile, Article, LanguageCertificate, NextEducationMajor
from django.contrib.auth.admin import UserAdmin



class ProfileInline(admin.StackedInline):
    model = Profile

class EducationProfileInline(admin.StackedInline):
    model = EducationProfile

class ArticleInline(admin.StackedInline):
    model = Article

class LanguageCertificateInline(admin.StackedInline):
    model = LanguageCertificate

class NextEducationMajorAdmin(admin.ModelAdmin):
    list_display = ('name',)

class UserAdmin(UserAdmin):
    inlines = [ProfileInline, EducationProfileInline, ArticleInline, LanguageCertificateInline]

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(NextEducationMajor, NextEducationMajorAdmin)

