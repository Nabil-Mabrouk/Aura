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
    "login_timeout": 30, 
    "network_timeout": 30,
}

# --- FastAPI Setup ---
class ComponentRequest(BaseModel):
    component_name: str

app = FastAPI(
    title="AURA Procedure Agent (Snowflake-Connected)",
    description="Fetches SOPs directly from an enterprise Snowflake data warehouse."
)
def get_from_snowflake(component_name: str):
    """Primary Method: Tries to fetch from Snowflake."""
    print(f"PROCEDURE AGENT: Attempting to fetch '{component_name}' from Snowflake (Primary)...")
    try:
        with snowflake.connector.connect(**SNOWFLAKE_CREDS) as conn:
            with conn.cursor() as cur:
                query = "SELECT procedure_id, steps, safety_warnings FROM PROCEDURES WHERE component_name ILIKE %s"
                cur.execute(query, (component_name,)) # Use ILIKE for case-insensitive search
                result = cur.fetchone()
        if result:
            print("PROCEDURE AGENT: Success! Found procedure in Snowflake.")
            procedure_id, steps_json, warnings_json = result
            return {
                "status": "success",
                "data": {
                    "procedure_id": procedure_id,
                    "steps": json.loads(steps_json),
                    "safety_warnings": json.loads(warnings_json),
                },
                "source": "Snowflake (Live)"
            }
        return None # Return None if not found, to trigger fallback
    except Exception as e:
        print(f"PROCEDURE AGENT: Snowflake connection failed: {e}")
        return None # Return None on any failure, to trigger fallback

def get_from_local_db(component_name: str):
    """Fallback Method: Tries to fetch from the local SQLite cache."""
    print(f"PROCEDURE AGENT: Fallback! Attempting to fetch '{component_name}' from local cache...")
    try:
        response = requests.get(SUPERVISOR_API_URL, params={'component_name': component_name}, timeout=5)
        if response.status_code == 200:
            print("PROCEDURE AGENT: Success! Found procedure in local cache.")
            data = response.json()
            data['source'] = "Local Cache (Offline)"
            return { "status": "success", "data": data }
        return None # Return None if not found (e.g., 404 from supervisor)
    except Exception as e:
        print(f"PROCEDURE AGENT: Local cache fetch failed: {e}")
        return None

@app.post("/get_procedure")
async def get_procedure(request: ComponentRequest):
    component = request.component_name
    
    # 1. Try online source first
    procedure_data = get_from_snowflake(component)
    
    # 2. If it fails, try the offline fallback
    if not procedure_data:
        procedure_data = get_from_local_db(component)

    # 3. If BOTH sources fail, return a graceful "not found" message.
    if not procedure_data:
        print(f"PROCEDURE AGENT: Procedure for '{component}' not found in any data source.")
        return {
            "status": "error",
            "message": f"No procedure found for component '{component}' in any available knowledge base."
        }
        
    # 4. If either source succeeded, return the data.
    return procedure_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)