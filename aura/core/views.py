# aura_supervisor/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Job, JobLog
from .services import (
    call_identifier_agent, 
    call_procedure_agent, 
    call_summarizer_agent,
    AgentInteractionError
)
import threading
import time

def job_list(request):
    """Displays a list of all jobs."""
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'core/job_list.html', {'jobs': jobs})

def job_detail(request, job_id):
    """Displays the detail page for a single job."""
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'core/job_detail.html', {'job': job})

def job_detail_log_api(request, job_id):
    """An API endpoint to fetch the latest logs for a job, used by the frontend."""
    job = get_object_or_404(Job, id=job_id)
    logs = job.logs.all().values('timestamp', 'source', 'message')
    return JsonResponse({'status': job.get_status_display(), 'logs': list(logs)})


def run_job_workflow(job_id):
    """
    This is the main agentic workflow, run in a separate thread
    to avoid blocking the web request.
    """
    job = Job.objects.get(id=job_id)

    def log(source, message, metadata=None):
        JobLog.objects.create(job=job, source=source, message=message, metadata=metadata)

    try:
        job.status = Job.Status.IN_PROGRESS
        job.save()

        log(JobLog.Source.SUPERVISOR, "Job started. Initializing agent workflow...")

        # --- Step 1: Identify Component ---
        log(JobLog.Source.SUPERVISOR, "Delegating to Identifier Agent to analyze visual feed...")
        # We pass fake image data for now
        id_response = call_identifier_agent(image_data=b"fake_image_bytes")
        identified_component = id_response.get("component")
        job.identified_component = identified_component
        job.save()
        log(JobLog.Source.IDENTIFIER, f"Component identified: {identified_component}", metadata=id_response)

        # --- Step 2: Retrieve Procedure ---
        log(JobLog.Source.SUPERVISOR, "Delegating to Procedure Agent to fetch SOP from Snowflake...")
        proc_response = call_procedure_agent(component_name=identified_component)
        steps = proc_response.get("steps", [])
        log(JobLog.Source.PROCEDURE, f"Retrieved procedure with {len(steps)} steps.", metadata=proc_response)

        # --- Step 3: Guide Technician (Simulated) ---
        log(JobLog.Source.SUPERVISOR, "Displaying steps to technician and awaiting visual confirmation...")
        for i, step in enumerate(steps):
            log(JobLog.Source.SUPERVISOR, f"Step {i+1}: {step}")
            # In a real app, we would wait for user input/confirmation here
            time.sleep(0.5) # Simulate time taken for each step
        log(JobLog.Source.USER, "All steps confirmed as completed by technician.")
        
        # --- Step 4: Summarize ---
        log_history = "\n".join([f"[{l.source}] {l.message}" for l in job.logs.all()])
        log(JobLog.Source.SUPERVISOR, "Delegating to Summarizer Agent for final report...")
        summary_response = call_summarizer_agent(job_log_text=log_history)
        job.final_summary = summary_response.get("summary")
        log(JobLog.Source.SUMMARIZER, "Final summary generated.", metadata=summary_response)

        # --- Step 5: Finish ---
        job.status = Job.Status.COMPLETED
        job.save()
        log(JobLog.Source.SUPERVISOR, "Job workflow completed successfully.")

    except AgentInteractionError as e:
        job.status = Job.Status.FAILED
        job.save()
        log(JobLog.Source.SUPERVISOR, f"Workflow failed: {e}")
    except Exception as e:
        job.status = Job.Status.FAILED
        job.save()
        log(JobLog.Source.SUPERVISOR, f"An unexpected error occurred: {e}")


def create_and_run_job(request):
    """
    A view that creates a new job and starts its workflow in the background.
    """
    if request.method == 'POST':
        new_job = Job.objects.create()
        # Run the long-running task in a separate thread
        thread = threading.Thread(target=run_job_workflow, args=(new_job.id,))
        thread.start()
        return redirect('core:job_detail', job_id=new_job.id)
    
    # If not a POST request, redirect to the job list
    return redirect('job_list')