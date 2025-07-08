from langchain_core.tools import tool
from . import services
import base64
import magic
from .models import Interaction, Job  # <-- Import the Job model



@tool
def identify_objects_in_image(interaction_id: str) -> dict:
    """
    Call this tool with the ID of the interaction containing the image to be analyzed.
    This tool "sees" the image and returns a list of detected objects.
    """
    print(f"--- TOOL: identify_objects_in_image for interaction {interaction_id} ---")
    try:
        interaction = Interaction.objects.get(id=interaction_id)
        if not interaction.user_image_input:
            return {"error": "The specified interaction does not contain an image."}
        
        with interaction.user_image_input.open('rb') as f:
            image_bytes = f.read()
            mime_type = magic.from_buffer(image_bytes, mime=True)
            print(f"--- TOOL: Detected image MIME type as: {mime_type} ---")

            # Now, construct the data URL with the CORRECT MIME type
            base64_encoded_data = base64.b64encode(image_bytes).decode('utf-8')
            image_base64 = f"data:{mime_type};base64,{base64_encoded_data}"
        
        return services.call_identifier_agent(image_base64)
    except Interaction.DoesNotExist:
        return {"error": f"Could not find interaction with ID {interaction_id}."}

@tool
def get_procedure_for_component(component_name: str) -> dict:
    """
    Call this tool with the exact name of a component to get its official procedure
    from the enterprise knowledge base.
    """
    print(f"--- TOOL: get_procedure_for_component for '{component_name}' ---")
    return services.call_procedure_agent(component_name)

@tool
def annotate_image_with_boxes(interaction_id: str, boxes: list) -> dict:
    """
    Call this tool to draw bounding boxes on an image from a specific interaction.
    Provide the interaction ID and a list of box objects to draw.
    Each box object should be a dictionary with 'label' and 'box' keys.
    """
    print(f"--- TOOL: annotate_image_with_boxes for interaction {interaction_id} ---")
    try:
        interaction = Interaction.objects.get(id=interaction_id)
        if not interaction.user_image_input:
            return {"error": "The specified interaction does not contain an image to annotate."}

        with interaction.user_image_input.open('rb') as f:
            image_bytes = f.read()
            image_base64 = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

        return services.call_annotator_agent(image_base64, boxes)
    except Interaction.DoesNotExist:
        return {"error": f"Could not find interaction with ID {interaction_id}."}

@tool
def describe_image_content(interaction_id: str) -> dict:
    """
    Call this tool with the ID of the interaction containing the image to be analyzed.
    This tool "sees" the image using a Vision Language Model and returns a rich textual description.
    """
    print(f"--- TOOL: describe_image_content for interaction {interaction_id} ---")
    try:
        interaction = Interaction.objects.get(id=interaction_id)
        if not interaction.user_image_input:
            return {"error": "The specified interaction does not contain an image."}
        
        # Open the image file from Django's storage
        with interaction.user_image_input.open('rb') as f:
            image_bytes = f.read()

            # --- DYNAMIC MIME TYPE DETECTION ---
            # Use python-magic to detect the MIME type from the file's content
            mime_type = magic.from_buffer(image_bytes, mime=True)
            print(f"--- TOOL: Detected image MIME type as: {mime_type} ---")
            
            # Now, construct the data URL with the CORRECT MIME type
            base64_encoded_data = base64.b64encode(image_bytes).decode('utf-8')
            image_base64 = f"data:{mime_type};base64,{base64_encoded_data}"
        
        # The rest of the function remains the same
        return services.call_groq_llama_vision_agent(image_base64)
        
    except Interaction.DoesNotExist:
        return {"error": f"Could not find interaction with ID {interaction_id}."}
    except Exception as e:
        return {"error": f"An unexpected error occurred in the tool: {str(e)}"}
@tool
def end_session_and_generate_report(job_id: str, outcome: str) -> str:
    """
    Call this tool ONLY when the user indicates the entire task is complete.
    This tool ends the session, generates a final summary report, and closes the job.
    The 'outcome' argument must be either 'success' or 'failure', based on the conversation.
    """
    print(f"--- TOOL: end_session_and_generate_report for Job {job_id} with outcome: {outcome} ---")
    try:
        job = Job.objects.get(id=job_id)
        
        # Build the conversation log for the summarizer
        history_list = [f"{inter.source}: {inter.user_text_input or inter.aura_text_response}" for inter in job.interactions.order_by('timestamp')]
        full_log_text = "\n".join(history_list)
        
        try:
            summary_response = services.call_summarizer_agent(full_log_text)
            final_summary = summary_response.get("summary", "Summary could not be generated.")
        except services.AgentInteractionError as e:
            final_summary = f"Summary could not be generated due to an agent error: {e}"

        job.final_report_text = final_summary
        
        if outcome.lower() == 'success':
            job.status = Job.Status.COMPLETED_SUCCESS
        else:
            job.status = Job.Status.COMPLETED_FAILURE
        job.save()

        response_message = f"SESSION ENDED with status '{job.get_status_display()}'. The final report has been generated. The session is now closed."
        
        # Log this final action to the interaction history
        Interaction.objects.create(job=job, source=Interaction.Source.AURA, aura_text_response=response_message)
        
        return response_message
    except Job.DoesNotExist:
        return f"Error: Could not find a job with the ID {job_id}."    
all_tools = [
    identify_objects_in_image,
    get_procedure_for_component,
    annotate_image_with_boxes,
    describe_image_content,
    end_session_and_generate_report, # <-- Add the new tool
]