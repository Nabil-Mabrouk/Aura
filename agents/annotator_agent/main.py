# agents/annotator_agent/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import base64
from PIL import Image, ImageDraw
import io

class Box(BaseModel):
    label: str
    box: List[int] = Field(..., min_items=4, max_items=4)

class AnnotateRequest(BaseModel):
    image_base64: str
    boxes: List[Box]

app = FastAPI(title="AURA Annotator Agent")

@app.post("/annotate")
async def annotate_image(request: AnnotateRequest):
    try:
        header, encoded = request.image_base64.split(",", 1)
        image_data = io.BytesIO(base64.b64decode(encoded))
        image = Image.open(image_data).convert("RGB")
        draw = ImageDraw.Draw(image)

        for item in request.boxes:
            box = tuple(item.box)
            # Draw the bounding box
            draw.rectangle(box, outline="lime", width=3)
            # Draw the label with a background
            text_position = (box[0], box[1] - 15)
            text_bbox = draw.textbbox(text_position, item.label)
            draw.rectangle(text_bbox, fill="lime")
            draw.text(text_position, item.label, fill="black")

        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return {"annotated_image_base64": f"data:image/jpeg;base64,{img_str}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))