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
    responses={
        201: {"description": "Employee created"},
        400: {"model": schemas.Problem, "description": "Validation error"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    """
    Create a new employee.

    Example request
    {
      "first_name": "John",
      "last_name": "Doe",
      "gender": true,
      "birth_date": "1990-01-01",
      "idp_id": "auth0|abc123"
    }
    """
    return crud.create_employee(db, payload)

@router.get(
    "/",
    response_model=List[schemas.EmployeeOut],
    summary="List active employees",
    responses={
        200: {"description": "Employees retrieved"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def list_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Paginated list of active employees."""
    return crud.get_employees(db, skip=skip, limit=limit)

@router.get(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Get employee by ID",
    responses={
        200: {"description": "Employee found"},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """Fetch a single employee by numeric ID."""
    emp = crud.get_employee(db, employee_id)
    if not emp or not emp.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp

@router.put(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Update employee",
    responses={
        200: {"description": "Employee updated"},
        400: {"model": schemas.Problem, "description": "Validation error"},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def update_employee(employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db)):
    """
    Update full employee record. All fields in EmployeeUpdate are required.

    Example request
    {
      "idp_id": null,
      "first_name": "Jane",
      "last_name": "Doe",
      "gender": false,
      "birth_date": "1992-02-02",
      "id_picture": null,
      "active": true
    }
    """
    emp = crud.update_employee(db, employee_id, payload)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp

@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete (soft) employee",
    responses={
        204: {"description": "Employee deactivated"},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Soft-delete an employee by setting active to false."""
    emp = crud.soft_delete_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

# ─── Inter-service example: reservations for an employee ───────────────────────

@router.get(
    "/{employee_id}/reservations",
    response_model=List[schemas.Reservation],
    summary="List reservations for employee (via reservation service)",
    responses={
        200: {"description": "Reservations retrieved"},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        502: {"model": schemas.Problem, "description": "Upstream reservation service error"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
async def get_reservations(employee_id: int, db: Session = Depends(get_db)):
    """
    Proxy call to the Reservation service. Requires RESERVATION_SERVICE_URL in the environment.
    """
    emp = crud.get_employee(db, employee_id)
    if not emp or not emp.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    client = ReservationServiceClient()
    try:
        return await client.get_reservations_for_employee(employee_id)
    except Exception as e:
        # Surface as Bad Gateway to indicate upstream failure
        raise HTTPException(status_code=502, detail=f"Reservation service error: {e}")

# ─── File: picture upload (thumbnail generated) ────────────────────────────────

@router.post(
    "/{employee_id}/picture",
    response_model=schemas.EmployeeOut,
    summary="Upload/update employee picture & generate thumbnail",
    responses={
        200: {"description": "Thumbnail generated and employee updated"},
        400: {"model": schemas.Problem, "description": "Invalid image"},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
async def upload_picture(
    employee_id: int,
    file: UploadFile = File(..., description="Image file (png or jpeg recommended)"),
    db: Session = Depends(get_db),
):
    """
    Example multipart/form-data
    file: (binary)
    """
    emp = crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    try:
        url = await LocalStorage.save_and_thumbnail(file, employee_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {e}")

    emp.id_picture = url
    db.commit()
    db.refresh(emp)

    return emp
