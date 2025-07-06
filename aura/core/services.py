# aura/core/services.py
import requests

# --- NEW DOCKER-FRIENDLY ENDPOINTS ---
# The hostname is now the service name from docker-compose.yml
# AGENT_ENDPOINTS = {
#     "identifier": "http://identifier_agent:8001/identify",
#     "procedure": "http://procedure_agent:8002/get_procedure",
#     "summarizer": "http://summarizer_agent:8003/summarize"
# }
AGENT_ENDPOINTS = {
    "identifier": "http://host.docker.internal:8001/identify",
    "procedure": "http://host.docker.internal:8002/get_procedure",
    "summarizer": "http://host.docker.internal:8003/summarize",
    "command": "http://host.docker.internal:8004/parse_command" # For Day 3
}
# ... the rest of the file remains exactly the same ...
# (The functions will now use these new URLs)
class AgentInteractionError(Exception):
    """Custom exception for agent communication failures."""
    pass

def call_identifier_agent():
    """Calls the Identifier Agent via its Docker service name."""
    try:
        url = AGENT_ENDPOINTS["identifier"]
        print(f"SUPERVISOR: Calling Identifier Agent inside Docker at {url}...")
        response = requests.post(url, json={'image_placeholder': 'simulated_image.jpg'})
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