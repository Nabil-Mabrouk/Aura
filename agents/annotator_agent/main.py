# agents/annotator_agent/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import cv2
import numpy as np
import base64
from typing import List

# --- Pydantic Models for Input/Output Data Structures ---

class BoundingBox(BaseModel):
    """
    Defines the structure for a single object's bounding box and label.
    This must match the structure returned by the Identifier Agent.
    """
    box: List[int] = Field(..., description="[x1, y1, x2, y2] coordinates")
    label: str
    confidence: float

class AnnotateRequest(BaseModel):
    """
    Defines the expected input: the original image and a list of boxes to draw.
    """
    image_base64: str
    boxes: List[BoundingBox]

class AnnotateResponse(BaseModel):
    """
    Defines the successful response: the new, annotated image as a base64 string.
    """
    annotated_image_base64: str
    agent_name: str = "AnnotatorAgent/v1.0-OpenCV"

# --- FastAPI Application Setup ---

app = FastAPI(
    title="AURA Annotator Agent (OpenCV)",
    description="A specialized agent that draws bounding boxes and labels on an image.",
)

# --- Image Conversion Helper Functions ---

def base64_to_image(b64_string: str) -> np.ndarray:
    """Decodes a base64 data URL string into an OpenCV compatible numpy array."""
    if "," in b64_string:
        b64_string = b64_string.split(',')[1]
    img_bytes = base64.b64decode(b64_string)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image

def image_to_base64(image: np.ndarray) -> str:
    """Encodes an OpenCV image (numpy array) into a base64 data URL string."""
    # Encode the image as a JPEG in memory
    _, buffer = cv2.imencode('.jpg', image)
    # Convert the buffer to a base64 string
    b64_string = base64.b64encode(buffer).decode('utf-8')
    # Prepend the data URL header
    return f"data:image/jpeg;base64,{b64_string}"

# --- Main Annotation Endpoint ---

@app.post("/annotate", response_model=AnnotateResponse)
async def draw_boxes_on_image(request: AnnotateRequest):
    """
    This endpoint receives a base64 image and a list of bounding boxes,
    draws them on the image, and returns the annotated image as a base64 string.
    """
    try:
        # Step 1: Decode the incoming image string into a usable format.
        print("ANNOTATOR AGENT: Decoding image from base64...")
        image = base64_to_image(request.image_base64)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data.")

        # Step 2: Iterate through the bounding boxes and draw them.
        print(f"ANNOTATOR AGENT: Drawing {len(request.boxes)} boxes on the image...")
        for b_box in request.boxes:
            # Bounding box coordinates
            x1, y1, x2, y2 = b_box.box
            label = b_box.label
            confidence = b_box.confidence
            
            # Define color and thickness for the box
            box_color = (0, 255, 0) # Green
            box_thickness = 2
            
            # Draw the rectangle on the image
            cv2.rectangle(image, (x1, y1), (x2, y2), box_color, box_thickness)
            
            # --- Draw the label with a filled background for readability ---
            label_text = f"{label}: {confidence:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 1
            
            # Get the size of the text to create a background box
            (text_width, text_height), baseline = cv2.getTextSize(label_text, font, font_scale, font_thickness)
            
            # Position the background rectangle just above the bounding box
            label_bg_y2 = y1 - baseline
            label_bg_y1 = label_bg_y2 - text_height - 6 # Add some padding
            
            # Draw the filled rectangle for the label background
            cv2.rectangle(image, (x1, label_bg_y1), (x1 + text_width + 4, label_bg_y2 + 4), box_color, -1) # -1 thickness for filled
            
            # Draw the text on top of the background
            cv2.putText(image, label_text, (x1 + 2, label_bg_y2), font, font_scale, (0, 0, 0), font_thickness) # Black text

        # Step 3: Encode the modified image back to base64.
        print("ANNOTATOR AGENT: Encoding annotated image to base64...")
        annotated_image_b64 = image_to_base64(image)

        # Step 4: Return the structured response.
        return AnnotateResponse(annotated_image_base64=annotated_image_b64)

    except Exception as e:
        error_message = f"Failed to annotate image: {str(e)}"
        print(f"ANNOTATOR AGENT: An unexpected error occurred: {error_message}")
        raise HTTPException(status_code=500, detail=error_message)


# This block allows running the agent directly for testing purposes.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)