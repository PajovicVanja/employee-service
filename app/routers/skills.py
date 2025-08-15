from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.dependencies import get_db
from app.services.company_client import CompanyServiceClient

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
    employee_id: int = Path(..., description="Employee ID"),
    db: Session = Depends(get_db)
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
    employee_id: int = Path(..., description="Employee ID"),
    service_ids: List[int] = Body(
        ...,
        description="List of service IDs that this employee can perform",
        examples={"basic": {"summary": "Replace with three services", "value": [1, 3, 5]}},
    ),
    db: Session = Depends(get_db),
):
    """
    Example request
    [1, 3, 5]
    """
    emp = crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # If we know the employee's company, ensure services belong to it
    c = CompanyServiceClient()
    if c.enabled() and emp.company_id:
        valid_services = c.services_set_for_company(emp.company_id)
        for sid in service_ids:
            if sid not in valid_services:
                raise HTTPException(
                    status_code=400,
                    detail=f"service_id {sid} does not belong to company_id {emp.company_id}"
                )

    return crud.replace_skills(db, employee_id, service_ids)
