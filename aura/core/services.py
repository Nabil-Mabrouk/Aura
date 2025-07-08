# aura/core/services.py
import requests
import base64
from typing import List, Dict, Any
import json

# AGENT_ENDPOINTS now points to the services that will be running on the host machine,
# launched by the Coral Server. The supervisor container will access them via the
# special 'host.docker.internal' DNS name.
AGENT_ENDPOINTS = {
    "identifier": "http://host.docker.internal:8001/identify",
    "procedure": "http://host.docker.internal:8002/get_procedure",
    "summarizer": "http://host.docker.internal:8003/summarize",
    "command": "http://host.docker.internal:8004/parse_command", 
    "annotator": "http://host.docker.internal:8005/annotate",
    "groq_llama_vision": "http://host.docker.internal:8006/identify",
}

class AgentInteractionError(Exception):
    """Custom exception for agent communication failures."""
    pass

def call_identifier_agent(image_base64: str) -> Dict[str, Any]:
    """
    Calls the upgraded Identifier Agent.
    
    Args:
        image_base64 (str): The base64 encoded image string from the frontend.

    Returns:
        Dict[str, Any]: The JSON response from the agent, containing detected objects.
    """
    try:
        url = AGENT_ENDPOINTS["identifier"]
        print(f"SUPERVISOR: Calling Identifier Agent with image data at {url}...")
        
        # The agent now expects a JSON payload with the base64 string.
        payload = {'image_base64': image_base64}
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AgentInteractionError(f"Identifier Agent at {url} failed: {e}")
    
def call_groq_llama_vision_agent(image_base64: str) -> Dict[str, Any]:
    """
    Calls the upgraded Identifier Agent.
    
    Args:
        image_base64 (str): The base64 encoded image string from the frontend.

    Returns:
        Dict[str, Any]: The JSON response from the agent, containing detected objects.
    """
    try:
        url = AGENT_ENDPOINTS["groq_llama_vision"]
        print(f"SUPERVISOR: Calling Groq Llama Vision Agent with image data at {url}...")

        # The agent now expects a JSON payload with the base64 string.
        payload = {'image_base64': image_base64}
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AgentInteractionError(f"Identifier Agent at {url} failed: {e}")

def call_procedure_agent(component_name: str):
    """Calls the Procedure Agent via its Docker service name."""
    try:
        url = AGENT_ENDPOINTS["procedure"]
        print(f"SUPERVISOR: Calling Procedure Agent inside Docker at {url}...")
        response = requests.post(url, json={'component_name': component_name})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AgentInteractionError(f"Procedure Agent at {url} failed: {e}")

def call_summarizer_agent(job_log_text: str):
    """Calls the Summarizer Agent via its Docker service name."""
    try:
        url = AGENT_ENDPOINTS["summarizer"]
        print(f"SUPERVISOR: Calling Summarizer Agent inside Docker at {url}...")
        response = requests.post(url, json={'log_text': job_log_text})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AgentInteractionError(f"Summarizer Agent at {url} failed: {e}")

# New function to call the command agent
def call_command_agent(history: list, new_text: str, has_image: bool):
    """Calls the Command Agent to parse user intent with Groq/Llama."""
    try:
        url = AGENT_ENDPOINTS["command"]
        print(f"SUPERVISOR: Calling Command Agent at {url}...")
        payload = {
            "history": history,
            "new_text": new_text,
            "has_image": has_image,
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        # Get the raw text from the response body.
        return response.text
    except json.JSONDecodeError as e:
        raise AgentInteractionError(f"Command Agent returned invalid JSON: {response.text}")
def call_annotator_agent(image_base64: str, boxes: list):
    try:
        url = AGENT_ENDPOINTS["annotator"]
        print(f"SUPERVISOR: Calling Annotator Agent at {url}...")
        payload = {"image_base64": image_base64, "boxes": boxes}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AgentInteractionError(f"Annotator Agent at {url} failed: {e}")