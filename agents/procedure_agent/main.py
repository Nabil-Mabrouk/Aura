# agents/procedure_agent/main.py

# --- START OF ENVIRONMENT FIX ---
# This block runs BEFORE any other imports to fix the "homeless" environment issue.
import os
import pathlib

# Check if the HOME environment variable is missing.
if not os.getenv("HOME") and not os.getenv("USERPROFILE"):
    print("PROCEDURE AGENT: HOME/USERPROFILE not set. Attempting to set it automatically.")
    try:
        # Use pathlib to find the user's home directory in a cross-platform way.
        home_dir = pathlib.Path.home()
        # Set the environment variable for this process.
        os.environ['USERPROFILE'] = str(home_dir)
        os.environ['HOME'] = str(home_dir)
        print(f"PROCEDURE AGENT: Successfully set HOME to {home_dir}")
    except RuntimeError as e:
        # If even pathlib fails, we cannot proceed.
        print(f"PROCEDURE AGENT: CRITICAL ERROR - Could not determine home directory. {e}")
        # Exit with an error code to prevent the server from starting incorrectly.
        exit(1)
# --- END OF ENVIRONMENT FIX ---


# Now, with the environment fixed, we can safely import everything else.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import json
from dotenv import load_dotenv
import snowflake.connector
import requests
# Load environment variables from .env file (for Snowflake credentials)
load_dotenv()

# --- Snowflake Connection Details from Environment ---
SNOWFLAKE_CREDS = {
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
}

# --- FastAPI Setup ---
class ComponentRequest(BaseModel):
    component_name: str

app = FastAPI(
    title="AURA Procedure Agent (Snowflake-Connected)",
    description="Fetches SOPs directly from an enterprise Snowflake data warehouse."
)
def get_procedure_from_snowflake(component_name: str):
    """Primary Method: Tries to fetch the procedure from Snowflake."""
    print("PROCEDURE AGENT: Attempting to fetch from Snowflake (Primary)...")
    conn = None
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CREDS)
        with conn.cursor() as cur:
            query = "SELECT procedure_id, steps, safety_warnings FROM PROCEDURES WHERE component_name = %s"
            cur.execute(query, (component_name,))
            result = cur.fetchone()
        conn.close()
        
        if result:
            print("PROCEDURE AGENT: Success! Found procedure in Snowflake.")
            procedure_id, steps_json, warnings_json = result
            return {
                "procedure_id": procedure_id,
                "steps": json.loads(steps_json),
                "safety_warnings": json.loads(warnings_json),
                "source": "Snowflake (Live)"
            }
        return None
    except Exception as e:
        print(f"PROCEDURE AGENT: Snowflake connection failed: {e}")
        if conn and not conn.is_closed():
            conn.close()
        return None

def get_procedure_from_local_db(component_name: str):
    """Fallback Method: Tries to fetch from the local SQLite DB via an API call to the Supervisor."""
    print("PROCEDURE AGENT: Fallback! Attempting to fetch from local cache via Supervisor API...")
    try:
        # The supervisor needs a new API endpoint to expose this data
        # We assume the supervisor runs on the host from the agent's perspective
        supervisor_api_url = "http://host.docker.internal:8000/app/api/local_procedure/"
        response = requests.get(supervisor_api_url, params={'component_name': component_name})
        response.raise_for_status()
        
        data = response.json()
        print("PROCEDURE AGENT: Success! Found procedure in local cache.")
        data['source'] = "Local Cache (Offline)"
        return data
    except Exception as e:
        print(f"PROCEDURE AGENT: Local cache fetch failed: {e}")
        return None

@app.post("/get_procedure")
async def get_procedure(request: ComponentRequest):
    component = request.component_name
    
    # Try online source first
    procedure_data = get_procedure_from_snowflake(component)
    
    # If it fails, try the offline fallback
    if not procedure_data:
        procedure_data = get_procedure_from_local_db(component)

    if not procedure_data:
        raise HTTPException(status_code=404, detail="Procedure not found in any data source.")
        
    return procedure_data

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)