# app/services/storage.py
import os, io
from PIL import Image
from fastapi import UploadFile

# Base on-disk root (you can override with STORAGE_PATH in .env)
ROOT = os.getenv("STORAGE_PATH", "storage")
ORIG_DIR = os.path.join(ROOT, "originals")
THUMB_DIR = os.path.join(ROOT, "thumbnails")

# Make sure the dirs exist
for d in (ORIG_DIR, THUMB_DIR):
    os.makedirs(d, exist_ok=True)

class LocalStorage:
    @staticmethod
    async def save_and_thumbnail(file: UploadFile, employee_id: int) -> str:
        # read bytes
        data = await file.read()
        # infer extension
        ext = file.content_type.split("/")[-1]
        orig_path = os.path.join(ORIG_DIR, f"{employee_id}.{ext}")
        with open(orig_path, "wb") as f:
            f.write(data)

        # generate 128×128 thumbnail
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((128, 128))
        thumb_path = os.path.join(THUMB_DIR, f"{employee_id}.jpg")
        img.save(thumb_path, format="JPEG")

        # return the *public* URL to the thumbnail
        return f"/files/thumbnails/{employee_id}.jpg"
