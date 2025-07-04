# landing/views.py
from django.shortcuts import render

def landing_page(request):
    """Renders the main landing page."""
    return render(request, 'landing/landing_page.html')