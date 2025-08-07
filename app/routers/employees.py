import os
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.dependencies import get_db
from app.services.interop_client import ReservationServiceClient
from app.services.storage import LocalStorage

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
async def create_employee(emp_in: schemas.EmployeeCreate, db: Session = Depends(get_db)):
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
    summary="Upload/update employee picture & generate thumbnail",
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}},
)
async def upload_picture(
    employee_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Save the upload locally, generate 128×128 thumbnail, and record URL.
    """
    emp = crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # save & thumbnail
    url = await LocalStorage.save_and_thumbnail(file, employee_id)

    # persist
    emp.id_picture = url
    db.commit()
    db.refresh(emp)

    return emp
