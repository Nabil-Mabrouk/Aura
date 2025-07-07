# Aura/core/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Job, Interaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import services # Import your services module
import json
import base64

# --- Helper Functions for the View ---

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

# --- Main Views ---

def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'core/job_list.html', {'jobs': jobs})

def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'core/job_detail.html', {'job': job})

# This API now needs to be more intelligent
def job_detail_log_api(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    interactions = job.interactions.all()
    
    # We need to build a chronological log from the interaction objects
    log_entries = []
    for interaction in interactions:
        if interaction.user_text_input:
            log_entries.append({'source': 'USER', 'message': interaction.user_text_input, 'timestamp': interaction.timestamp})
        if interaction.aura_text_response:
            log_entries.append({'source': 'AURA', 'message': interaction.aura_text_response, 'timestamp': interaction.timestamp})
            
    # Sort by timestamp just in case
    log_entries.sort(key=lambda x: x['timestamp'])

    # Get the URL of the latest annotated image, if any
    latest_annotated_image_url = None
    # Find the last interaction from Aura that has an annotated image file
    last_aura_interaction_with_image = job.interactions.filter(
        source=Interaction.Source.AURA, 
        aura_annotated_image__isnull=False,
        aura_annotated_image__gt='' # Ensures the field is not just null, but not empty either
    ).last()
    
    # --- THIS IS THE FIX ---
    # Only try to get the URL if we found an interaction AND it has a file
    if last_aura_interaction_with_image and last_aura_interaction_with_image.aura_annotated_image:
        latest_annotated_image_url = last_aura_interaction_with_image.aura_annotated_image.url

    return JsonResponse({
        'status': job.get_status_display(), 
        'logs': log_entries,
        'latest_annotated_image_url': latest_annotated_image_url
    })

def create_job_session(request):
    if request.method == 'POST':
        new_job = Job.objects.create()
        return redirect('core:job_detail', job_id=new_job.id)
    return redirect('core:job_list')

@api_view(['POST'])
def handle_interaction_api(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    print("--- INTERACTION START ---")
    
    try:
        user_text = request.data.get('text', '')
        image_file = request.FILES.get('image')
        
        user_interaction = log_interaction(job, Interaction.Source.USER, text=user_text, image=image_file)
        print(f"1. User input logged. Text: '{user_text}', Image: {image_file is not None}")

        history = list(job.interactions.order_by('timestamp').values('user_text_input', 'aura_text_response'))
        
        # --- THINK STAGE ---
        print("2. Calling Command Agent...")
        intent_data_from_service = services.call_command_agent(history, user_text, has_image=bool(image_file))
        print(f"DEBUG: Received raw string from service: {intent_data_from_service}")
        print(f"DEBUG: Type of received data is: {type(intent_data_from_service)}")

        # --- THE FINAL, ROBUST PARSING LOGIC ---
        
        intent_data = intent_data_from_service
        # Keep trying to parse as long as the data is a string
        while isinstance(intent_data, str):
            print("DEBUG: Data is a string, attempting to parse as JSON...")
            try:
                intent_data = json.loads(intent_data)
            except json.JSONDecodeError:
                error_message = f"Failed to parse string from Command Agent: {intent_data}"
                print(error_message)
                raise services.AgentInteractionError(error_message)
        
        print(f"--- FINAL CHECK --- Final data type is: {type(intent_data)}")
        
        # This will now succeed regardless of what the agent sent.
        action = intent_data.get("action")
        parameters = intent_data.get("parameters", {})

        user_interaction.parsed_intent = action
        user_interaction.save()
        print(f"3. Command Agent responded. Action: {action}, Params: {parameters}")

        aura_response_text = "I'm on it."
        
        # --- ACTION STAGE ---
        if action == "IDENTIFY_AND_CLARIFY":
            if not user_interaction.user_image_input:
                aura_response_text = "Action requires an image, but none was provided. Please upload an image."
                print("4a. Action failed: IDENTIFY_AND_CLARIFY needs an image.")
            else:
                print("4a. Calling Identifier Agent...")
                # --- SEE STAGE ---
                with user_interaction.user_image_input.open('rb') as f:
                    image_bytes = f.read()
                    image_base64 = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                
                id_response = services.call_identifier_agent(image_base64)
                print(f"5. Identifier Agent responded.")
                
                detected_labels = [obj['label'] for obj in id_response.get('detected_objects', [])]
                
                if detected_labels:
                    aura_response_text = f"I see: {', '.join(detected_labels)}. Your request mentioned '{parameters.get('user_query')}'. Please confirm which component you mean."
                    print("6. Formulated clarifying question.")
                else:
                    aura_response_text = "I couldn't identify any known components in that image. Please try another picture."
                    print("6. No components identified.")

        elif action == "FETCH_PROCEDURE":
            print("4b. Calling Procedure Agent...")
            component = parameters.get("component_name")
            if component:
                proc_response = services.call_procedure_agent(component)
                steps = proc_response.get("steps", [])
                aura_response_text = f"Retrieved procedure for {component}. Step 1 is: {steps[0]}"
                print("5. Procedure Agent responded.")
            else:
                aura_response_text = "I was asked to fetch a procedure, but the component name was missing. Please clarify."
                print("5. Procedure Agent call failed: missing component name.")
        
        else:
            aura_response_text = f"I understood the action '{action}', but I don't know how to handle it yet."
            print(f"4c. Unhandled action: {action}")

        # --- LOG AURA'S RESPONSE ---
        log_interaction(job, Interaction.Source.AURA, text=aura_response_text)
        print("7. Aura's response logged.")

        return Response({"status": "ok", "aura_response": aura_response_text})

    except services.AgentInteractionError as e:
        error_message = f"An agent failed to respond. Error: {e}"
        print(f"--- WORKFLOW FAILED (Agent Error) ---\n{error_message}")
        log_interaction(job, Interaction.Source.AURA, text=error_message)
        return Response({"status": "error", "message": str(e)}, status=500)
    except Exception as e:
        import traceback
        error_message = f"A critical system error occurred. Error: {e}"
        print(f"--- WORKFLOW FAILED (System Error) ---\n{traceback.format_exc()}")
        log_interaction(job, Interaction.Source.AURA, text=error_message)
        return Response({"status": "error", "message": str(e)}, status=500)

# @api_view(['POST'])
# def handle_interaction_api(request, job_id):
#     """
#     The main orchestrator. This view handles a single turn of the conversation.
#     """
#     job = get_object_or_404(Job, id=job_id)
#     print("--- INTERACTION START ---")
#     # 1. Get user input from the request
#     user_text = request.data.get('text', '')
#     image_file = request.FILES.get('image')
    
#     # Log the user's turn
#     user_interaction = log_interaction(job, Interaction.Source.USER, text=user_text, image=image_file)


#     # 2. Prepare the "memory" for the Command Agent
#     history = []
#     # Query all previous interactions for this job
#     for inter in job.interactions.order_by('timestamp'):
#         if inter.user_text_input:
#             history.append({'user_text_input': inter.user_text_input, 'aura_text_response': None})
#         if inter.aura_text_response:
#             history.append({'user_text_input': None, 'aura_text_response': inter.aura_text_response})

#     # 3. Call the "Thinking" Agent (Groq/Llama)
#     try:
#         intent_data = services.call_command_agent(history, user_text, has_image=bool(image_file))
#         #intent_data = json.loads(intent_data_str) # The response is a stringified JSON
#         action = intent_data.get("action")
#         parameters = intent_data.get("parameters", {})
#         user_interaction.parsed_intent = action
#         user_interaction.save()

#         aura_response_text = "I'm processing that. One moment."
#         annotated_image_response = None

#         # 4. --- THE STATE MACHINE ORCHESTRATION ---
#         if action == "IDENTIFY_AND_CLARIFY":
#             # We need an image for this action
#             if not user_interaction.user_image_input:
#                 aura_response_text = "Please upload an image for me to identify components."
#             else:
#                 # Call the "Seeing" Agent
#                 with user_interaction.user_image_input.open('rb') as f:
#                     image_bytes = f.read()
#                     image_base64 = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                
#                 id_response = services.call_identifier_agent(image_base64)
#                 detected_labels = [obj['label'] for obj in id_response.get('detected_objects', [])]
                
#                 # Formulate the clarifying question
#                 if detected_labels:
#                     aura_response_text = f"I see the following components: {', '.join(detected_labels)}. Your request mentioned '{parameters.get('user_query')}'. Please confirm which component you'd like to proceed with."
#                 else:
#                     aura_response_text = "I wasn't able to identify any components in that image. Could you try a different angle or a clearer picture?"

#         elif action == "FETCH_PROCEDURE":
#             component = parameters.get("component_name")
#             if component:
#                 # Call the Procedure Agent to get data from Snowflake
#                 proc_response = services.call_procedure_agent(component)
#                 steps = proc_response.get("steps", [])
#                 aura_response_text = f"Procedure for {component} retrieved. Step 1: {steps[0]}"
                
#                 # Here we could also call the Annotator agent to highlight the component
#                 # This is a great place for a stretch goal
#             else:
#                 aura_response_text = "I'm sorry, I'm not sure which component you are referring to. Could you be more specific?"

#         elif action == "ANSWER_QUESTION":
#              aura_response_text = f"Regarding your question about '{parameters.get('question')}': I am an operational assistant. For detailed technical questions, please consult the official documentation."
#              # A real implementation would call another Groq agent for RAG here.

#         else:
#             aura_response_text = "I've received your message, but I'm not sure how to proceed. Can you please rephrase?"

#         # Log Aura's turn
#         log_interaction(job, Interaction.Source.AURA, text=aura_response_text)
        
#         return Response({"status": "ok"})

#     except services.AgentInteractionError as e:
#         log_interaction(job, Interaction.Source.AURA, text=f"An agent failed to respond. Please try again. Error: {e}")
#         return Response({"status": "error", "message": str(e)}, status=500)
#     except Exception as e:
#         log_interaction(job, Interaction.Source.AURA, text=f"A system error occurred. Error: {e}")
#         return Response({"status": "error", "message": str(e)}, status=500)