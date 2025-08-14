from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.dependencies import get_db

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.EmployeeSkillOut],
    summary="List employee skills",
    responses={
        200: {"description": "Skills list"},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def get_skills(
    employee_id: int, db: Session = Depends(get_db)
):
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    return crud.get_skills(db, employee_id)

@router.put(
    "/",
    response_model=List[schemas.EmployeeSkillOut],
    summary="Replace employee skills",
    responses={
        200: {"description": "Skills replaced"},
        400: {"model": schemas.Problem, "description": "Validation error"},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def replace_skills(
    employee_id: int,
    service_ids: List[int],
    db: Session = Depends(get_db),
):
    """
    Example request
    [1, 3, 5]
    """
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    return crud.replace_skills(db, employee_id, service_ids)
