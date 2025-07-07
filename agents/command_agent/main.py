from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from groq import Groq
from dotenv import load_dotenv
import json # <-- Add this import
from fastapi.responses import JSONResponse
# Load environment variables from .env file
load_dotenv()

# --- Pydantic Models for Input Validation ---
class InteractionHistory(BaseModel):
    user_text_input: str | None = None
    aura_text_response: str | None = None

class CommandRequest(BaseModel):
    history: list[InteractionHistory]
    new_text: str
    has_image: bool

# --- Groq Client Initialization ---
try:
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    groq_client = None

# --- FastAPI App ---
app = FastAPI(
    title="AURA Command Agent",
    description="The central 'thinking' agent that parses user intent using Groq/Llama.",
)

# agents/command_agent/main.py

SYSTEM_PROMPT = """
You are the central command unit for an AI assistant named AURA. Your job is to analyze a conversation and decide the single next action.
You MUST respond with ONLY a valid JSON object. Do not add any conversational text or markdown.
You must analyze the FULL conversation history, especially AURA's last response, to understand the current state of the conversation.

**Conversation States and Actions:**

1.  **Initial State (No history or user is starting over):**
    - If the user provides an initial command and an image, your action MUST be `IDENTIFY_AND_CLARIFY`.
    - This tells the supervisor to identify all objects and ask the user to confirm the target based on their query.
    - **Required JSON:** `{"action": "IDENTIFY_AND_CLARIFY", "parameters": {"user_query": "The user's original request text"}}`

2.  **Clarification State (AURA's last response was a question like "Which component do you mean?"):**
    - If the user's new input answers this question (e.g., "the keyboard," "the one on the left," "yes"), your action MUST be `FETCH_PROCEDURE`.
    - You must infer the specific component name from the user's answer and the context.
    - **Required JSON:** `{"action": "FETCH_PROCEDURE", "parameters": {"component_name": "The specific component name, e.g., 'keyboard' or 'CPU'"}}`

3.  **General Question State:**
    - If the user asks a general question not related to confirming a step.
    - Action: `ANSWER_QUESTION`.
    - **Required JSON:** `{"action": "ANSWER_QUESTION", "parameters": {"question": "The user's question text"}}`

**Example 1 (Initial State):**
User's first input: "Help me replace the graphics card."
Your JSON response:
{"action": "IDENTIFY_AND_CLARIFY", "parameters": {"user_query": "replace the graphics card"}}

**Example 2 (Clarification State):**
History: [{"aura_text_response": "I see a GPU and a RAM stick. Did you mean the GPU?"}]
User's new input: "Yes, that's the one."
Your JSON response:
{"action": "FETCH_PROCEDURE", "parameters": {"component_name": "GPU"}}
"""

@app.post("/parse_command")
async def parse_command(request: CommandRequest):
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq client not initialized. Check API key.")

    # Format the history for the prompt
    formatted_history = "\n".join([
        f"- User: {h.user_text_input}" for h in request.history if h.user_text_input
    ] + [
        f"- Aura: {h.aura_text_response}" for h in request.history if h.aura_text_response
    ])

    prompt = f"Conversation History:\n{formatted_history}\n\nUser's latest input: '{request.new_text}'"

    try:
        print("COMMAND AGENT: Sending request to Groq...")
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model="llama3-8b-8192",
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        response_content_str = chat_completion.choices[0].message.content
        print(f"COMMAND AGENT: Received from Groq: {response_content_str}")
        response_data = json.loads(response_content_str)
        return JSONResponse(content=response_data)
    except Exception as e:
        print(f"COMMAND AGENT: Error calling Groq API: {e}")
        raise HTTPException(status_code=500, detail=str(e))