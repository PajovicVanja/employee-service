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
        200: {"description": "Skills list",
              "content": {"application/json": {"example": [{"service_id": 7}, {"service_id": 9}]}}},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def get_skills(
    employee_id: int = Path(..., description="Employee ID", example=1),
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
        200: {"description": "Skills replaced",
              "content": {"application/json": {"example": [{"service_id": 1}, {"service_id": 3}, {"service_id": 5}]}}},
        400: {"model": schemas.Problem, "description": "Validation error (service not in employee's company)",
              "content": {"application/json": {"example": {
                  "type": "about:blank", "title": "Validation error", "status": 400,
                  "detail": "service_id 42 does not belong to company_id 1",
                  "instance": "/employees/1/skills/"
              }}}},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def replace_skills(
    employee_id: int = Path(..., description="Employee ID", example=1),
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
