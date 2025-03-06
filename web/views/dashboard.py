import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.conf import settings
from django.contrib.auth.models import Group
from web import helpers

TEMPLATE_DIR = 'dashboard'


@login_required(login_url=settings.LOGIN_URL)
def dashboard(request):
    context = {
        'students_count': helpers.students.count(),
        'teachers_count': helpers.teachers.count(),
        'admins_count': helpers.admins.count(),
    }
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'), context)