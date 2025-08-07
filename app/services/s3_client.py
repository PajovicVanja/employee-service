import os
from minio import Minio
from fastapi import UploadFile

class S3ClientService:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT").replace("http://", "").replace("https://", ""),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=os.getenv("MINIO_ENDPOINT", "").startswith("https://")
        )
        self.bucket = os.getenv("MINIO_BUCKET")

    async def upload_picture(self, file: UploadFile, employee_id: int) -> str:
        ext = file.filename.split(".")[-1]
        object_name = f"employees/{employee_id}/profile_{employee_id}.{ext}"
        data = await file.read()
        self.client.put_object(self.bucket, object_name, data, length=len(data), content_type=file.content_type)
        return f"{os.getenv('MINIO_ENDPOINT')}/{self.bucket}/{object_name}"
