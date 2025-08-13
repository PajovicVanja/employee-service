from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.dependencies import get_db

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.AvailabilitySlotOut],
    summary="List availability slots",
    responses={404: {"description": "Employee not found"}},
)
def list_availability(
    employee_id: int, db: Session = Depends(get_db)
):
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return crud.get_availability(db, employee_id)

@router.post(
    "/",
    response_model=List[schemas.AvailabilitySlotOut],
    summary="Add availability slots",
    responses={404: {"description": "Employee not found"}},
)
def add_availability(
    employee_id: int,
    slots: List[schemas.AvailabilitySlotCreate],
    db: Session = Depends(get_db),
):
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return crud.create_availability(db, employee_id, slots)

@router.delete(
    "/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an availability slot",
    responses={404: {"description": "Employee or slot not found"}},
)
def remove_availability(
    employee_id: int, slot_id: int, db: Session = Depends(get_db)
):
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    slot = crud.delete_availability_slot(db, slot_id)
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
