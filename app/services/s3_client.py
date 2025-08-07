# app/services/s3_client.py

import os
import io
from minio import Minio
from fastapi import UploadFile

__all__ = ["S3ClientService"]

class S3ClientService:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT").replace("http://", "").replace("https://", ""),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=os.getenv("MINIO_ENDPOINT", "").startswith("https://"),
        )
        self.bucket = os.getenv("MINIO_BUCKET")

    async def upload_picture(self, file: UploadFile, employee_id: int) -> str:
        """
        Legacy: upload directly from an UploadFile.
        """
        data = await file.read()
        return await self.upload_picture_bytes(data, file.content_type, employee_id)

    async def upload_picture_bytes(
        self,
        data: bytes,
        content_type: str,
        employee_id: int,
    ) -> str:
        """
        Upload raw bytes (e.g. from a read() call) as the employee's picture.
        """
        # infer extension from content_type (e.g. image/jpeg → jpeg)
        ext = content_type.split("/")[-1]
        object_name = f"employees/{employee_id}/profile_{employee_id}.{ext}"
        # stream bytes into MinIO
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return f"{os.getenv('MINIO_ENDPOINT').rstrip('/')}/{self.bucket}/{object_name}"
