# thumbnail-function/handler.py
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from app.services.storage import LocalStorage

app = FastAPI(title="Thumbnail Generator")

@app.post("/thumbnail")
async def create_thumbnail(
    file: UploadFile = File(...),
    employee_id: int = Query(..., description="Employee ID to tag thumbnail under"),
):
    # delegate to your local-storage service
    try:
        url = await LocalStorage.save_and_thumbnail(file, employee_id)
    except Exception as e:
        raise HTTPException(400, f"Error processing image: {e}")
    return {"thumbnail_url": url}
