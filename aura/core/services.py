# aura/core/services.py
import requests
import time

# --- Agent Endpoints (Now the first one is real!) ---
IDENTIFIER_AGENT_URL = "http://127.0.0.1:8001/identify"
PROCEDURE_AGENT_URL = "http://127.0.0.1:8002/get_procedure"
SUMMARIZER_AGENT_URL = "http://127.0.0.1:8003/summarize"

class AgentInteractionError(Exception):
    """Custom exception for when an agent fails."""
    pass

def call_identifier_agent(image_data=None):
    """
    Calls the REAL Identifier Agent to identify a component.
    """
    try:
        print("SUPERVISOR: Calling Identifier Agent at", IDENTIFIER_AGENT_URL)
        
        # --- THIS IS THE CHANGE ---
        # The 'files' part is how you'd send a real file. Even though our
        # agent ignores it, it's good practice to send it.
        response = requests.post(IDENTIFIER_AGENT_URL, files={'image': b'fake_image_bytes'})
        
        # Check if the request was successful
        response.raise_for_status() 
        
        # Return the JSON response from the agent
        return response.json()

    except requests.RequestException as e:
        # This will now catch errors if the agent isn't running!
        raise AgentInteractionError(f"Identifier Agent failed: {e}")

def call_procedure_agent(component_name):
    """
    Calls the REAL Procedure Agent to get the official runbook/SOP.
    """
    try:
        print(f"SUPERVISOR: Calling Procedure Agent for component: {component_name} at {PROCEDURE_AGENT_URL}")
        
        # --- THIS IS THE CHANGE ---
        # We send a JSON payload this time
        response = requests.post(PROCEDURE_AGENT_URL, json={'component_name': component_name})
        
        # Check if the request was successful
        response.raise_for_status() 
        
        # Return the JSON response from the agent
        return response.json()

    except requests.RequestException as e:
        raise AgentInteractionError(f"Procedure Agent failed: {e}")


def call_summarizer_agent(job_log_text):
    """
    Calls the REAL Summarizer Agent to create a final report.
    """
    try:
        print(f"SUPERVISOR: Calling Summarizer Agent at {SUMMARIZER_AGENT_URL}...")
        
        # We send the full log history as a JSON payload
        response = requests.post(SUMMARIZER_AGENT_URL, json={'log_text': job_log_text})
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the JSON response from the agent
        return response.json()
        
    except requests.RequestException as e:
        raise AgentInteractionError(f"Summarizer Agent failed: {e}")