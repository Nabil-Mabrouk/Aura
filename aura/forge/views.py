# Aura/forge/views.py
from django.shortcuts import render

def forge_view(request):
    """
    Renders the AURA Forge page, which demonstrates the conceptual
    pipeline for training a custom vision model.
    """
    # We can pass context here later if needed, but for now, it's just rendering.
    context = {}
    return render(request, 'forge/forge.html', context)