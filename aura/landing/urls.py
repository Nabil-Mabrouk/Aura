# landing/urls.py
from django.urls import path
from . import views

app_name = 'landing' # <-- Add this for namespacing

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
]