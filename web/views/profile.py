import os
from django.shortcuts import render

TEMPLATE_DIR = 'profile'

def profile(request):
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'))
