# Aura/core/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from langchain_core.messages import HumanMessage, AIMessage
from .models import Job, Interaction
from . import services
from .langchain_agent import create_aura_agent_executor
import json
import base64
import traceback
import os
from .models import Procedure

# --- Create a single, global instance of our agent executor ---
print("--- Initializing AURA LangChain Agent Executor ---")
aura_agent_executor = create_aura_agent_executor()
print("--- AURA Agent Executor Initialized ---")

# --- Helper Functions ---

def log_interaction(job, source, text=None, image=None, intent=None, annotated_image=None):
    """A helper to cleanly create Interaction log entries."""
    interaction = Interaction.objects.create(
        job=job,
        source=source,
        user_text_input=text if source == Interaction.Source.USER else None,
        user_image_input=image if source == Interaction.Source.USER else None,
        aura_text_response=text if source == Interaction.Source.AURA else None,
        aura_annotated_image=annotated_image if source == Interaction.Source.AURA else None,
        parsed_intent=intent
    )
    return interaction

def save_base64_image_to_field(field, base64_str, filename):
    """Decodes a base64 string and saves it to a Django ImageField."""
    if not base64_str or "data:image" not in base64_str:
        return
    try:
        format, imgstr = base64_str.split(';base64,') 
        ext = format.split('/')[-1] 
        data = ContentFile(base64.b64decode(imgstr), name=f'{filename}.{ext}')
        field.save(data.name, data, save=True)
    except Exception as e:
        print(f"Error saving base64 image: {e}")


# --- Main Page Views ---

def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'core/job_list.html', {'jobs': jobs})

def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'core/job_detail.html', {'job': job})

def create_job_session(request):
    """Creates a new Job (Session) and a welcome message, then redirects."""
    if request.method == 'POST':
        new_job = Job.objects.create()
        # Create an initial welcome message from Aura
        log_interaction(
            job=new_job, 
            source=Interaction.Source.AURA, 
            text="New session started. Please provide an image and your instructions."
        )
        return redirect('core:job_detail', job_id=new_job.id)
    return redirect('core:job_list')


# --- Session Management Views ---

def end_session(request, job_id, outcome):
    """Ends a session, calls the summarizer, and updates the job status."""
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        history_list = []
        for inter in job.interactions.order_by('timestamp'):
            if inter.user_text_input:
                history_list.append(f"USER: {inter.user_text_input}")
            if inter.aura_text_response:
                history_list.append(f"AURA: {inter.aura_text_response}")
        
        full_log_text = "\n".join(history_list)
        
        try:
            summary_response = services.call_summarizer_agent(full_log_text)
            final_summary = summary_response.get("summary", "Summary could not be generated.")
        except services.AgentInteractionError as e:
            final_summary = f"Summary could not be generated due to an agent error: {e}"

        job.final_report_text = final_summary
        if outcome == 'success':
            job.status = Job.Status.COMPLETED_SUCCESS
        else:
            job.status = Job.Status.COMPLETED_FAILURE
        job.save()

        log_interaction(job, Interaction.Source.AURA, text=f"SESSION ENDED: {job.get_status_display()}. Final report generated.")
    return redirect('core:job_list')

def delete_session(request, job_id):
    """Deletes a session and all related interactions."""
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        job.delete()
    return redirect('core:job_list')


# --- API Views ---

@api_view(['GET'])
def job_detail_log_api(request, job_id):
    """API endpoint to fetch the conversational log for the live UI."""
    job = get_object_or_404(Job, id=job_id)
    interactions = job.interactions.all().order_by('timestamp')
    log_entries = []
    latest_annotated_image_url = None

    for interaction in interactions:
        if interaction.user_text_input:
            log_entries.append({'source': 'USER', 'message': interaction.user_text_input, 'timestamp': interaction.timestamp.isoformat()})
        if interaction.aura_text_response:
            log_entries.append({'source': 'AURA', 'message': interaction.aura_text_response, 'timestamp': interaction.timestamp.isoformat()})
        if interaction.aura_annotated_image and interaction.aura_annotated_image.url:
            latest_annotated_image_url = interaction.aura_annotated_image.url
            
    return JsonResponse({
        'status': job.get_status_display(), 
        'logs': log_entries,
        'latest_annotated_image_url': latest_annotated_image_url
    })

@api_view(['POST'])
def handle_interaction_api(request, job_id):
    """The main orchestrator view that bridges the UI to the LangChain Agent."""
    job = get_object_or_404(Job, id=job_id)
    
    try:
        user_text = request.data.get('text', '')
        image_file = request.FILES.get('image')
        
        user_interaction = Interaction.objects.create(
            job=job, source=Interaction.Source.USER, 
            user_text_input=user_text, user_image_input=image_file
        )
        print(f"--- INTERACTION START for Job {job_id} ---")

        chat_history = []
        # Get all interactions EXCEPT the one we just created
        previous_interactions = job.interactions.exclude(id=user_interaction.id).order_by('timestamp')

        for inter in previous_interactions:
            if inter.user_text_input:
                chat_history.append(HumanMessage(content=inter.user_text_input))
            if inter.aura_text_response:
                chat_history.append(AIMessage(content=inter.aura_text_response))
        
        final_input_string = user_text

        if user_interaction.user_image_input:
            # We are now explicitly telling the LLM the ID it MUST use.
            final_input_string += f"\n\n[SYSTEM CONTEXT: An image has been provided for this turn. To analyze it, you MUST call the `identify_objects_in_image` tool with this exact ID: '{user_interaction.id}']"

        # 3. Prepare the main input for the agent executor
        agent_input = {
            "input": user_text, 
            "chat_history": chat_history,
            # --- THIS IS THE FIX ---
            # Pass the interaction_id at the top level of the input.
            # The agent can now access this value.
            #"interaction_id": str(user_interaction.id)
        }
        # if user_interaction.user_image_input:
        #     agent_input["input"] += f"\n\n[CONTEXT: An image was provided for this turn. The interaction ID is: {user_interaction.id}]"

        print(f"Invoking AURA LangChain Agent Executor...")
        response = aura_agent_executor.invoke(agent_input)
        print(f"Agent Executor finished. Full response: {response}")
        
        aura_response_text = response.get("output", "I'm sorry, I encountered an issue.")
        
        annotated_image_b64 = None
        if 'intermediate_steps' in response:
            for action, observation in response['intermediate_steps']:
                if action.tool == 'annotate_image_with_boxes' and isinstance(observation, dict):
                    annotated_image_b64 = observation.get('annotated_image_base64')

        aura_interaction = Interaction(job=job, source=Interaction.Source.AURA, aura_text_response=aura_response_text)
        if annotated_image_b64:
            save_base64_image_to_field(aura_interaction.aura_annotated_image, annotated_image_b64, f"anno_{user_interaction.id}")
        aura_interaction.save()
        
        return Response({"status": "ok"})

    except Exception as e:
        error_message = f"A critical system error occurred in the orchestrator: {e}"
        print(f"--- WORKFLOW FAILED (System Error) ---\n{traceback.format_exc()}")
        Interaction.objects.create(job=job, source=Interaction.Source.AURA, aura_text_response=error_message)
        return Response({"status": "error", "message": str(e)}, status=500)

# --- ADD THIS NEW VIEW FUNCTION ---
@api_view(['GET']) # This view only needs to handle GET requests
def local_procedure_api(request):
    """
    An API endpoint for agents to query the local cache of procedures
    as an offline fallback.
    """
    component_name = request.query_params.get('component_name', None)
    
    if not component_name:
        return Response({"error": "component_name parameter is required"}, status=400)
    
    try:
        # Query the local Procedure model
        procedure = Procedure.objects.get(component_name=component_name)
        
        # Manually construct the response dictionary
        response_data = {
            "procedure_id": procedure.procedure_id,
            "steps": procedure.steps, # This is already a list from the JSONField
            "safety_warnings": procedure.safety_warnings,
        }
        return Response(response_data)
        
    except Procedure.DoesNotExist:
        return Response({"error": "Procedure not found in local cache"}, status=404)