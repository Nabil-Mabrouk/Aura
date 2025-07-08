# core/urls.py

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

    path('job/<uuid:job_id>/end/<str:outcome>/', views.end_session, name='end_session'),
    path('job/<uuid:job_id>/delete/', views.delete_session, name='delete_session'),

    path('api/local_procedure/', views.local_procedure_api, name='local_procedure_api'),
]