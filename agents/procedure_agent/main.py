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

@app.post("/get_procedure")
async def get_procedure(request: ComponentRequest):
    # The rest of this function remains the same as our working version
    print(f"PROCEDURE AGENT: Received request for component: {request.component_name}")
    print("PROCEDURE AGENT: Connecting to Snowflake...")
    conn = None
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CREDS)
        print("PROCEDURE AGENT: Snowflake connection successful.")
        with conn.cursor() as cur:
            query = "SELECT procedure_id, steps, safety_warnings FROM PROCEDURES WHERE component_name = %s"
            cur.execute(query, (request.component_name,))
            result = cur.fetchone()

        if result is None:
            raise HTTPException(status_code=404, detail="Procedure not found.")
        
        procedure_id, steps_json, warnings_json = result
        procedure_data = {
            "procedure_id": procedure_id,
            "steps": json.loads(steps_json),
            "safety_warnings": json.loads(warnings_json),
            "agent_name": "ProcedureAgent/v1.2-SelfFixing"
        }
        return procedure_data
    except snowflake.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn and not conn.is_closed():
            conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)