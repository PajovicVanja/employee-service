# app/routers/employees.py
import os
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.dependencies import get_db
from app.services.storage import LocalStorage
from app.services.interop_client import ReservationServiceClient

router = APIRouter()

# … your existing CRUD endpoints …

@router.post(
    "/{employee_id}/picture",
    response_model=schemas.EmployeeOut,
    summary="Upload/update employee picture & generate thumbnail",
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}},
)
async def upload_picture(
    employee_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    emp = crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # save to ./storage and create thumbnail
    url = await LocalStorage.save_and_thumbnail(file, employee_id)

    # record the thumbnail URL on the employee
    emp.id_picture = url
    db.commit()
    db.refresh(emp)

    return emp
