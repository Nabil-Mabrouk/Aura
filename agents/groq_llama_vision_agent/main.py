# agents/identifier_agent/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from groq import Groq
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# --- Pydantic Models for the New VLM-based Agent ---

class IdentifyRequest(BaseModel):
    """The request model remains the same, accepting a base64 data URL."""
    image_base64: str

class LlamaVisionResponse(BaseModel):
    """
    The new response model. Instead of bounding boxes, it returns a rich
    textual description of the image's content.
    """
    description: str = Field(
        ..., 
        description="A detailed textual description of the image content, focusing on key components and their states."
    )
    agent_name: str = "IdentifierAgent/v2.0-LlamaVision"

# --- Groq Client and Model Initialization ---
# --- Groq Client Initialization ---

# Load the Groq API key from environment variables.
# For local testing, you can create a .env file with GROQ_API_KEY="your-key"
# and run the agent with a loader like `uvicorn main:app --env-file .env`
try:
    print("IDENTIFIER AGENT: Initializing Groq client...")
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    # This is the hypothetical model name you provided.
    MODEL_NAME = "llama-4-scout-17b-16e-instruct" 
    print(f"IDENTIFIER AGENT: Groq client initialized for model {MODEL_NAME}.")
except Exception as e:
    print(f"FATAL: Could not initialize Groq client. Is GROQ_API_KEY set? Error: {e}")
    client = None

# This is the system prompt that guides the VLM to give us the desired output.
SYSTEM_PROMPT = """
You are a specialist AI Identifier Agent for the AURA system.
Your sole purpose is to analyze images of industrial environments (refineries, power plants, etc.)
and provide a concise, factual, and structured description.

- Start with a single-sentence overview of the scene.
- Use a bulleted list to identify key components, machinery, and any visible labels or text.
- Describe the apparent state of the components (e.g., "operational", "idle", "leaking steam").
- Be objective and descriptive. Do not offer opinions or suggestions.
"""

# --- FastAPI Application Setup ---

app = FastAPI(
    title="AURA Identifier Agent (Llama Vision)",
    description="A specialized agent to 'see' and describe components from visual data using a Vision Language Model.",
)

@app.post("/identify", response_model=LlamaVisionResponse)
async def identify_image_content(request: IdentifyRequest):
    """
    This endpoint receives a base64 encoded image, sends it to the Groq Llama
    vision model, and returns a rich textual description.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Groq client is not available.")

    print("IDENTIFIER AGENT: Received request. Preparing to call Groq VLM...")
    
    try:
        # The Groq API expects the image data URL directly.
        image_data_url = request.image_base64

        # Step 1: Call the Groq chat completions API with the image and prompt.
        # We use stream=False to get the complete response in a single API call.
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze the attached image and provide your description."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            temperature=0.2, # Lower temperature for more factual, less creative descriptions
            max_tokens=1024,
            top_p=1,
            stream=False # Important for a standard API request/response
        )

        # Step 2: Extract the text description from the response.
        description = completion.choices[0].message.content
        print(f"IDENTIFIER AGENT: Successfully received description from Groq.")

        # Step 3: Return the structured response.
        return LlamaVisionResponse(description=description)

    except Exception as e:
        # Catch-all for API errors, network issues, etc.
        error_message = f"Failed to get description from Groq VLM: {str(e)}"
        print(f"IDENTIFIER AGENT: An error occurred: {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

# This block allows running the agent directly for testing purposes.
if __name__ == "__main__":
    print("Starting Uvicorn server for Llama Vision Identifier Agent...")
    print("Ensure your GROQ_API_KEY is available as an environment variable.")
    uvicorn.run(app, host="0.0.0.0", port=8006)