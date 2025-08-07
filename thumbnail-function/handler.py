# thumbnail-function/handler.py

import os
import io
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from minio import Minio
from PIL import Image

app = FastAPI(title="Employee Thumbnail Generator")

# Init MinIO client from env
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT").replace("http://", "").replace("https://", ""),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_ENDPOINT", "").startswith("https://"),
)

THUMBNAIL_BUCKET = os.getenv("MINIO_THUMBNAIL_BUCKET", "employee-thumbnails")

@app.on_event("startup")
def ensure_bucket():
    # Create bucket if it doesn't exist
    if not minio_client.bucket_exists(THUMBNAIL_BUCKET):
        minio_client.make_bucket(THUMBNAIL_BUCKET)

@app.post("/thumbnail", summary="Generate & store a 128×128 thumbnail")
async def create_thumbnail(
    file: UploadFile = File(..., description="Original employee picture"),
    employee_id: int = Query(..., description="ID of the employee")
):
    # 1) Read + validate image
    try:
        data = await file.read()
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
    except Exception:
        raise HTTPException(400, "Uploaded file is not a valid image")

    # 2) Resize to thumbnail
    img.thumbnail((128, 128))

    # 3) Write into an in-memory buffer
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    # 4) Define object name & upload
    object_name = f"employees/{employee_id}/thumbnail.jpg"
    minio_client.put_object(
        bucket_name=THUMBNAIL_BUCKET,
        object_name=object_name,
        data=buf,
        length=buf.getbuffer().nbytes,
        content_type="image/jpeg",
    )

    # 5) Return the public URL
    endpoint = os.getenv("MINIO_ENDPOINT")
    url = f"{endpoint.rstrip('/')}/{THUMBNAIL_BUCKET}/{object_name}"
    return {"thumbnail_url": url}
