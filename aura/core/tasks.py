# aura/core/tasks.py
from celery import shared_task
import time
from .models import Job, JobLog
from .services import (
    call_identifier_agent,
    call_procedure_agent,
    call_summarizer_agent,
    AgentInteractionError
)

@shared_task
def run_job_workflow_task(job_id):
    """
    This is the Celery task that runs our agentic workflow in the background.
    """
    # The logic is EXACTLY THE SAME as the old run_job_workflow function.
    # We just add the @shared_task decorator.
    job = Job.objects.get(id=job_id)
    def log(source, message, metadata=None):
        JobLog.objects.create(job=job, source=source, message=message, metadata=metadata)
    try:
        job.status = Job.Status.IN_PROGRESS
        job.save()
        log(JobLog.Source.SUPERVISOR, "Job started. Awaiting agent responses...")
        time.sleep(2)
        log(JobLog.Source.SUPERVISOR, "Delegating to Identifier Agent...")
        id_response = call_identifier_agent()
        identified_component = id_response.get("component")
        job.identified_component = identified_component
        job.save()
        log(JobLog.Source.IDENTIFIER, f"Component identified: {identified_component}", metadata=id_response)
        log(JobLog.Source.SUPERVISOR, "Delegating to Procedure Agent...")
        proc_response = call_procedure_agent(component_name=identified_component)
        steps = proc_response.get("steps", [])
        log(JobLog.Source.PROCEDURE, f"Retrieved procedure with {len(steps)} steps.", metadata=proc_response)
        log(JobLog.Source.SUPERVISOR, "Displaying steps to technician...")
        for i, step in enumerate(steps):
            log(JobLog.Source.SUPERVISOR, f"Step {i+1}: {step}")
            time.sleep(0.5)
        log(JobLog.Source.USER, "All steps confirmed as completed by technician.")
        log_history = "\n".join([f"[{l.source}] {l.message}" for l in job.logs.all()])
        log(JobLog.Source.SUPERVISOR, "Delegating to Summarizer Agent...")
        summary_response = call_summarizer_agent(job_log_text=log_history)
        job.final_summary = summary_response.get("summary")
        log(JobLog.Source.SUMMARIZER, "Final summary generated.", metadata=summary_response)
        job.status = Job.Status.COMPLETED
        job.save()
        log(JobLog.Source.SUPERVISOR, "Job workflow completed successfully.")
    except AgentInteractionError as e:
        job.status = Job.Status.FAILED
        job.save()
        log(JobLog.Source.SUPERVISOR, f"WORKFLOW FAILED: {e}")
    except Exception as e:
        job.status = Job.Status.FAILED
        job.save()
        log(JobLog.Source.SUPERVISOR, f"An unexpected error occurred: {e}")