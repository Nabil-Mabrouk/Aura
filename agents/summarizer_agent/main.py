from fastapi import FastAPI
from pydantic import BaseModel
import time
import uvicorn
import os # Good practice to use os for clarity

# Define the input data model. The Supervisor will send a long string of all the logs.
class LogTextRequest(BaseModel):
    log_text: str

# Create the FastAPI app instance
app = FastAPI(
    title="AURA Summarizer Agent",
    description="A specialized agent to summarize job logs and create a final report."
)

@app.post("/summarize")
async def summarize(request: LogTextRequest):
    """
    Receives a string of job logs and returns a concise summary.
    For the hackathon, we simulate this with a hardcoded response.
    Later, this could be a call to a real LLM like Groq's Llama 3.
    """
    # The length of the log text is a good proxy for how much work was done
    log_length = len(request.log_text)
    
    print(f"SUMMARIZER AGENT: Received request with {log_length} characters of log data.")
    print("SUMMARIZER AGENT: Simulating summarization process (e.g., LLM call)...")
    
    time.sleep(1) 
    
    # Hardcoded response that matches what the Supervisor expects
    summary_data = {
        "summary": "++ Job completed successfully. Component NVIDIA RTX 4090 GPU was serviced according to official procedures. All steps were followed correctly and confirmed by the supervisor. The final report has been generated and logged.",
        "agent_name": "SummarizerAgent/v1.0"
    }
    
    print("SUMMARIZER AGENT: Summarization complete. Sending response.")
    return summary_data



# This allows running the script directly
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)