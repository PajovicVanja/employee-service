# app/routers/employees.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.dependencies import get_db
from app.services.storage import LocalStorage
from app.services.interop_client import ReservationServiceClient

router = APIRouter()

# ─── CRUD: Employees ───────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=schemas.EmployeeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee",
)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    return crud.create_employee(db, payload)

@router.get(
    "/",
    response_model=List[schemas.EmployeeOut],
    summary="List active employees",
)
def list_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_employees(db, skip=skip, limit=limit)

@router.get(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Get employee by ID",
)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = crud.get_employee(db, employee_id)
    if not emp or not emp.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp

@router.put(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Update employee",
)
def update_employee(employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db)):
    emp = crud.update_employee(db, employee_id, payload)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp

@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete (soft) employee",
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = crud.soft_delete_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

# ─── Inter-service example: reservations for an employee ───────────────────────

@router.get(
    "/{employee_id}/reservations",
    response_model=List[schemas.Reservation],
    summary="List reservations for employee (via reservation service)",
)
async def get_reservations(employee_id: int, db: Session = Depends(get_db)):
    emp = crud.get_employee(db, employee_id)
    if not emp or not emp.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    client = ReservationServiceClient()
    return await client.get_reservations_for_employee(employee_id)

# ─── File: picture upload (thumbnail generated) ────────────────────────────────

@router.post(
    "/{employee_id}/picture",
    response_model=schemas.EmployeeOut,
    summary="Upload/update employee picture & generate thumbnail",
    responses={404: {"description": "Not found"}},
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
