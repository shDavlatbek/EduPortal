import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.conf import settings

TEMPLATE_DIR = 'auth'





def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, _('invalid_credentials'))
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, os.path.join(TEMPLATE_DIR, 'login.html'))
