# aura_supervisor/urls.py
# core/urls.py
from django.urls import path
from . import views

app_name = 'core' # <-- Add this for namespacing

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('job/new/', views.create_and_run_job, name='create_and_run_job'),
    path('job/<uuid:job_id>/', views.job_detail, name='job_detail'),
    path('api/job/<uuid:job_id>/log/', views.job_detail_log_api, name='job_detail_log_api'),
]