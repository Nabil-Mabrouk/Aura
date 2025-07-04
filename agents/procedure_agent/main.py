from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import uvicorn

import os
import json # To parse the VARIANT data from Snowflake
from dotenv import load_dotenv
import snowflake.connector

# Load environment variables from .env file
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

# Define the input data model for type safety and validation
class ComponentRequest(BaseModel):
    component_name: str

# Create the FastAPI app instance
app = FastAPI(
    title="AURA Procedure Agent (Snowflake-Connected)",
    description="Fetches SOPs directly from an enterprise Snowflake data warehouse."
)

@app.post("/get_procedure")
async def get_procedure(request: ComponentRequest):
    """
    Receives a component name, queries Snowflake, and returns the procedure.
    """
    print(f"PROCEDURE AGENT: Received request for component: {request.component_name}")
    print("PROCEDURE AGENT: Connecting to Snowflake...")

    conn = None  # Initialize conn to None
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CREDS)
        print("PROCEDURE AGENT: Snowflake connection successful.")
        
        with conn.cursor() as cur:
            # Use parameter binding to prevent SQL injection
            query = "SELECT procedure_id, steps, safety_warnings FROM PROCEDURES WHERE component_name = %s"
            cur.execute(query, (request.component_name,))
            result = cur.fetchone()

        if result is None:
            print("PROCEDURE AGENT: No procedure found for this component.")
            raise HTTPException(status_code=404, detail="Procedure not found for this component.")

        print("PROCEDURE AGENT: Procedure found. Formatting response.")
        
        # Unpack the result from the database
        procedure_id, steps_json, warnings_json = result
        
        # The VARIANT columns come back as JSON strings, so we parse them
        steps_list = json.loads(steps_json)
        warnings_list = json.loads(warnings_json)
        
        procedure_data = {
            "procedure_id": procedure_id,
            "steps": steps_list,
            "safety_warnings": warnings_list,
            "agent_name": "ProcedureAgent/v1.1-Snowflake" # Version bump!
        }
        
        return procedure_data
    except snowflake.connector.Error as e:
        print(f"PROCEDURE AGENT: Snowflake Error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error.")
    finally:
        # Ensure the connection is always closed
        if conn and not conn.is_closed():
            conn.close()
            print("PROCEDURE AGENT: Snowflake connection closed.")

# This allows running the script directly
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)