# Aura/forge/urls.py
from django.urls import path
from . import views

# This is important for namespacing, just like in the core app
app_name = 'forge'

urlpatterns = [
    # The root of the forge app will point to our forge_view
    path('', views.forge_view, name='forge_view'),
]