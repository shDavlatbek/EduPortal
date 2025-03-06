import os
from django.shortcuts import render

TEMPLATE_DIR = 'report'

def report(request):
    return render(request, os.path.join(TEMPLATE_DIR, 'index.html'))
