# thumbnail-function/handler.py
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from app.services.storage import LocalStorage

# If STORAGE_PATH is set, storage.py will have created
#   STORAGE_PATH/thumbnails
# default to /tmp/storage to match storage.py’s default.
STORAGE_PATH = os.getenv("STORAGE_PATH", "/tmp/storage")
THUMB_DIR    = os.path.join(STORAGE_PATH, "thumbnails")

app = FastAPI(title="Thumbnail Generator")

# serve /thumbnails/<id>.jpg
app.mount("/thumbnails", StaticFiles(directory=THUMB_DIR), name="thumbnails")

@app.post("/thumbnail")
async def create_thumbnail(
    file: UploadFile = File(...),
    employee_id: int = Query(..., description="Employee ID to tag thumbnail under"),
):
    try:
        url = await LocalStorage.save_and_thumbnail(file, employee_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {e}")
    return {"thumbnail_url": url}
