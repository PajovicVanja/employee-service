# app/routers/employees.py

import os
import httpx

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.dependencies import get_db
from app.services.interop_client import ReservationServiceClient

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.EmployeeOut],
    summary="List employees",
    responses={401: {"description": "Unauthorized"}},
)
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_employees(db, skip, limit)


@router.get(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Get an employee by ID",
    responses={404: {"description": "Employee not found"}, 401: {"description": "Unauthorized"}},
)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp


@router.get(
    "/{employee_id}/reservations",
    response_model=List[schemas.Reservation],
    summary="Get reservations for employee",
    responses={404: {"description": "Employee not found"}, 401: {"description": "Unauthorized"}},
)
async def get_reservations(employee_id: int, db: Session = Depends(get_db)):
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    client = ReservationServiceClient()
    return await client.get_reservations_for_employee(employee_id)


@router.post(
    "/",
    response_model=schemas.EmployeeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
    responses={400: {"description": "Invalid input"}, 401: {"description": "Unauthorized"}},
)
async def create_employee(
    emp_in: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
):
    return crud.create_employee(db, emp_in)


@router.put(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Update an existing employee",
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}},
)
def update_employee(employee_id: int, emp_up: schemas.EmployeeUpdate, db: Session = Depends(get_db)):
    emp = crud.update_employee(db, employee_id, emp_up)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an employee",
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}},
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = crud.soft_delete_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")


@router.post(
    "/{employee_id}/picture",
    response_model=schemas.EmployeeOut,
    summary="Upload/update employee picture and asynchronously generate thumbnail",
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}},
)
async def upload_picture(
    employee_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a profile picture to MinIO, save its URL on the employee,
    and then call the thumbnail‐generator function in the background.
    """
    emp = crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # upload original
    from app.services.s3_client import S3ClientService
    data = await file.read()
    url = await S3ClientService().upload_picture_bytes(data, file.content_type, employee_id)

    emp.id_picture = url
    db.commit()
    db.refresh(emp)

    # trigger thumbnail generator
    thumb_fn = os.getenv("THUMBNAIL_FUNCTION_URL")
    if thumb_fn:
        background_tasks.add_task(_call_thumbnail_service, data, employee_id)

    return emp


async def _call_thumbnail_service(data: bytes, employee_id: int):
    """
    POST raw bytes to our thumbnail-function endpoint.
    """
    endpoint = os.getenv("THUMBNAIL_FUNCTION_URL").rstrip("/") + "/thumbnail"
    files = {"file": ("image", data, "application/octet-stream")}
    params = {"employee_id": employee_id}
    async with httpx.AsyncClient() as client:
        await client.post(endpoint, files=files, params=params)
