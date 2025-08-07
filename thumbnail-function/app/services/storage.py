# thumbnail-function/app/services/storage.py
import os, io
from PIL import Image
from fastapi import UploadFile

ROOT = os.getenv("STORAGE_PATH", "/tmp/storage")
ORIG_DIR = os.path.join(ROOT, "originals")
THUMB_DIR = os.path.join(ROOT, "thumbnails")

for d in (ORIG_DIR, THUMB_DIR):
    os.makedirs(d, exist_ok=True)

class LocalStorage:
    @staticmethod
    async def save_and_thumbnail(file: UploadFile, employee_id: int) -> str:
        data = await file.read()
        ext = file.content_type.split("/")[-1]
        orig_path = os.path.join(ORIG_DIR, f"{employee_id}.{ext}")
        with open(orig_path, "wb") as f:
            f.write(data)

        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((128, 128))
        thumb_path = os.path.join(THUMB_DIR, f"{employee_id}.jpg")
        img.save(thumb_path, format="JPEG")

        # return the *relative* path (you can serve /tmp/storage via StaticFiles if you like)
        return f"/thumbnails/{employee_id}.jpg"
