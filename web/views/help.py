import os
from django.shortcuts import render

TEMPLATE_DIR = 'help'

def help(request):
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'))
