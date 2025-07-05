import requests

class AgentInteractionError(Exception):
    """Custom exception for all agent communication failures."""
    pass

def call_identifier_agent():
    """Calls the Identifier Agent, which has been launched by the Coral Server."""
    try:
        url = "http://127.0.0.1:8001/identify"
        print(f"SUPERVISOR: Calling Identifier Agent directly at {url}...")
        # The agent expects a JSON payload. We send a placeholder.
        response = requests.post(url, json={'image_placeholder': 'simulated_image.jpg'})
        response.raise_for_status()  # Raise an exception for HTTP error codes
        return response.json()
    except requests.RequestException as e:
        raise AgentInteractionError(f"Identifier Agent at {url} failed: {e}")

def call_procedure_agent(component_name: str):
    """Calls the Procedure Agent (launched by Coral) to query Snowflake."""
    try:
        url = "http://127.0.0.1:8002/get_procedure"
        print(f"SUPERVISOR: Calling Procedure Agent directly at {url}...")
        response = requests.post(url, json={'component_name': component_name})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AgentInteractionError(f"Procedure Agent at {url} failed: {e}")

def call_summarizer_agent(job_log_text: str):
    """Calls the Summarizer Agent, which has been launched by the Coral Server."""
    try:
        url = "http://127.0.0.1:8003/summarize"
        print(f"SUPERVISOR: Calling Summarizer Agent directly at {url}...")
        response = requests.post(url, json={'log_text': job_log_text})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise AgentInteractionError(f"Summarizer Agent at {url} failed: {e}")