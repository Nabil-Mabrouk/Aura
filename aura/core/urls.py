# aura_supervisor/urls.py
# core/urls.py
# from django.urls import path
# from . import views

# app_name = 'core' # <-- Add this for namespacing

# urlpatterns = [
#     path('', views.job_list, name='job_list'),
#     path('job/new/', views.create_and_run_job, name='create_and_run_job'),
#     path('job/<uuid:job_id>/', views.job_detail, name='job_detail'),
#     path('api/job/<uuid:job_id>/log/', views.job_detail_log_api, name='job_detail_log_api'),
#     # New endpoint for handling voice commands from the frontend
#     path('api/job/<uuid:job_id>/voice_command/', views.handle_voice_command, name='handle_voice_command'),
# ]

# Aura/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    
    # This view will now only create the Job/Session object
    path('job/new/', views.create_job_session, name='create_job_session'), 
    
    # The detail view remains the same
    path('job/<uuid:job_id>/', views.job_detail, name='job_detail'),
    
    # The log polling API remains the same (it will now poll the Interaction model)
    path('api/job/<uuid:job_id>/log/', views.job_detail_log_api, name='job_detail_log_api'),
    
    # --- ADD THIS NEW ENDPOINT ---
    # This is the main endpoint for all back-and-forth conversation
    path('api/job/<uuid:job_id>/interact/', views.handle_interaction_api, name='handle_interaction_api'),
]