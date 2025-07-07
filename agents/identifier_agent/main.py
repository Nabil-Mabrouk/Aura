# agents/identifier_agent/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import cv2
import numpy as np
import base64
from ultralytics import YOLO
from typing import List

# --- Pydantic Models for Input/Output Data Structures ---

class IdentifyRequest(BaseModel):
    # The agent expects a JSON payload with a single key: 'image_base64'.
    # This string will be a data URL from the browser (e.g., "data:image/jpeg;base64,...").
    image_base64: str

class BoundingBox(BaseModel):
    # Defines the structure for a single detected object's bounding box.
    # Format is [x1, y1, x2, y2] for top-left and bottom-right corners.
    box: List[int]
    label: str
    confidence: float

class IdentifyResponse(BaseModel):
    # Defines the structure of the successful response from this agent.
    detected_objects: List[BoundingBox]
    agent_name: str = "IdentifierAgent/v1.1-YOLOv8"

# --- YOLOv8 Model Loading ---

# Load the YOLOv8 model once on application startup.
# This is highly efficient as it prevents reloading the model on every API call.
# The 'yolov8n.pt' file will be downloaded automatically by the library on first run
# if it's not already present in the agent's directory.
try:
    print("IDENTIFIER AGENT: Loading YOLOv8 model...")
    model = YOLO("yolov8n.pt")
    print("IDENTIFIER AGENT: YOLOv8 model loaded successfully.")
except Exception as e:
    print(f"FATAL: Could not load YOLOv8 model. Error: {e}")
    model = None

# --- FastAPI Application Setup ---

app = FastAPI(
    title="AURA Identifier Agent (YOLOv8)",
    description="A specialized agent to 'see' and identify components from visual data.",
)

def base64_to_image(b64_string: str) -> np.ndarray:
    """
    Decodes a base64 encoded image string into an OpenCV compatible numpy array.
    This function handles data URLs (e.g., from a browser's canvas.toDataURL()).
    """
    # Check if the string is a data URL and strip the header if it is.
    if "," in b64_string:
        b64_string = b64_string.split(',')[1]
    
    # Decode the base64 string into bytes.
    img_bytes = base64.b64decode(b64_string)
    
    # Convert the bytes into a numpy array.
    np_arr = np.frombuffer(img_bytes, np.uint8)
    
    # Decode the numpy array into an image using OpenCV.
    # cv2.IMREAD_COLOR ensures it's read as a 3-channel BGR image.
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image

@app.post("/identify", response_model=IdentifyResponse)
async def identify_component(request: IdentifyRequest):
    """
    This endpoint receives a base64 encoded image, runs YOLOv8 object detection,
    and returns a list of detected objects with their labels and coordinates.
    """
    # First, check if the model was loaded successfully during startup.
    if not model:
        raise HTTPException(status_code=500, detail="YOLOv8 model is not loaded or failed to load.")

    try:
        # Step 1: Decode the incoming image string into a usable format.
        print("IDENTIFIER AGENT: Decoding image from base64...")
        image = base64_to_image(request.image_base64)

        if image is None:
            # This can happen if the base64 string is malformed or not an image.
            raise HTTPException(status_code=400, detail="Invalid image data. Could not decode.")
        
        # Step 2: Run the YOLOv8 model inference on the decoded image.
        print("IDENTIFIER AGENT: Running YOLOv8 inference...")
        results = model(image)
        
        # Step 3: Process the inference results.
        print("IDENTIFIER AGENT: Processing detection results...")
        detected_objects = []
        # The 'results' object is a list of results (usually just one for a single image).
        for result in results:
            # result.boxes contains all the bounding box detections.
            for box in result.boxes:
                # Get the class ID and look up the class name (e.g., "person", "car").
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                
                # Get the bounding box coordinates [x1, y1, x2, y2].
                coords = [int(c) for c in box.xyxy[0]]
                
                # Create a BoundingBox object and add it to our list.
                detected_objects.append(
                    BoundingBox(
                        label=class_name,
                        confidence=float(box.conf[0]),
                        box=coords
                    )
                )
        
        print(f"IDENTIFIER AGENT: Detected {len(detected_objects)} objects.")
        
        # Step 4: Return the structured response.
        return IdentifyResponse(detected_objects=detected_objects)

    except Exception as e:
        # Catch-all for any other unexpected errors during processing.
        print(f"IDENTIFIER AGENT: An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

# This block allows running the agent directly for testing purposes.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)