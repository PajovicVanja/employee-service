# app/routers/employees.py
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, schemas
from app.dependencies import get_db
from app.services.reservation_client import ReservationServiceClient
from app.services.company_client import CompanyServiceClient

router = APIRouter()

def _validate_company_and_location(payload: schemas.EmployeeBase, client: CompanyServiceClient):
    if not client.enabled():
        return
    # company -> must exist if provided
    if payload.company_id is not None and not client.validate_company(payload.company_id):
        raise HTTPException(status_code=400, detail=f"company_id {payload.company_id} not found")
    # location -> must exist if provided
    if payload.location_id is not None and not client.validate_location(payload.location_id):
        raise HTTPException(status_code=400, detail=f"location_id {payload.location_id} not found")

# ─── CRUD: Employees ───────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=schemas.EmployeeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee",
    responses={
        201: {
            "description": "Employee created",
            "content": {"application/json": {"example": {
                "id": 1, "idp_id": None, "first_name": "John", "last_name": "Doe",
                "gender": True, "birth_date": "1990-01-01", "id_picture": None,
                "active": True, "company_id": 1, "location_id": 12,
                "availability": [], "skills": []
            }}}
        },
        400: {
            "model": schemas.Problem,
            "description": "Validation error (e.g., unknown company/location)",
            "content": {"application/json": {"example": {
                "type": "about:blank", "title": "Validation error",
                "status": 400, "detail": "company_id 999 not found", "instance": "/employees/"
            }}}
        },
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def create_employee(
    payload: schemas.EmployeeCreate = Body(
        ...,
        description="New employee payload",
        examples={
            "minimal": {"summary": "Minimal", "value": {
                "first_name": "John", "last_name": "Doe", "gender": True, "birth_date": "1990-01-01"
            }},
            "withIntegration": {"summary": "With company & location", "value": {
                "first_name": "Ana", "last_name": "Kovač", "gender": False, "birth_date": "1995-06-15",
                "company_id": 1, "location_id": 12
            }},
        }
    ),
    db: Session = Depends(get_db),
):
    """
    Create a new employee. If COMPANY_SERVICE_URL is configured, company_id and
    location_id (when provided) are validated against Company Service.
    """
    _validate_company_and_location(payload, CompanyServiceClient())
    emp = crud.create_employee(db, payload)
    return emp

@router.get(
    "/",
    response_model=List[schemas.EmployeeOut],
    summary="List active employees",
    responses={
        200: {"description": "Employees retrieved",
              "content": {"application/json": {"example": [{
                  "id": 1, "first_name": "John", "last_name": "Doe", "gender": True,
                  "birth_date": "1990-01-01", "active": True, "idp_id": None,
                  "id_picture": None, "company_id": 1, "location_id": 12,
                  "availability": [], "skills": []
              }]}}},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def list_employees(
    skip: int = Query(0, ge=0, description="Number of records to skip (pagination)", example=0),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return", example=50),
    db: Session = Depends(get_db),
):
    """Paginated list of active employees."""
    return crud.get_employees(db, skip=skip, limit=limit)

@router.get(
    "/{employee_id}",
    response_model=schemas.EmployeeOut,
    summary="Get employee by ID",
    responses={
        200: {"description": "Employee found",
              "content": {"application/json": {"example": {
                  "id": 1, "first_name": "John", "last_name": "Doe", "gender": True,
                  "birth_date": "1990-01-01", "active": True, "idp_id": None,
                  "id_picture": None, "company_id": 1, "location_id": 12,
                  "availability": [], "skills": []
              }}}},
        404: {"model": schemas.Problem, "description": "Employee not found",
              "content": {"application/json": {"example": {
                  "type": "about:blank", "title": "Employee not found", "status": 404,
                  "instance": "/employees/999"
              }}}},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def get_employee(
    employee_id: int = Path(..., description="Employee ID", example=1),
    db: Session = Depends(get_db)
):
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
        200: {"description": "Employee updated",
              "content": {"application/json": {"example": {
                  "id": 1, "first_name": "Jane", "last_name": "Doe", "gender": False,
                  "birth_date": "1992-02-02", "active": True, "idp_id": None,
                  "id_picture": None, "company_id": 1, "location_id": 12,
                  "availability": [], "skills": []
              }}}},
        400: {"model": schemas.Problem, "description": "Validation error"},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def update_employee(
    employee_id: int = Path(..., description="Employee ID", example=1),
    payload: schemas.EmployeeUpdate = Body(
        ..., description="Full employee payload to replace existing data",
        examples={"example": {"summary": "Replace full record", "value": {
            "first_name": "Jane", "last_name": "Doe", "gender": False,
            "birth_date": "1992-02-02", "active": True, "company_id": 1, "location_id": 12
        }}}
    ),
    db: Session = Depends(get_db),
):
    """
    Update full employee record (validation against Company Service when configured).
    """
    _validate_company_and_location(payload, CompanyServiceClient())
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
def delete_employee(
    employee_id: int = Path(..., description="Employee ID", example=1),
    db: Session = Depends(get_db),
):
    """Soft-delete an employee by setting active to false."""
    emp = crud.soft_delete_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

@router.get(
    "/{employee_id}/reservations",
    response_model=List[schemas.Reservation],
    summary="List reservations for employee (via reservation service)",
    responses={
        200: {"description": "Reservations retrieved",
              "content": {"application/json": {"example": [{
                  "id": 555, "employee_id": 1, "date": "2025-01-01", "time_from": "09:00:00", "time_to": "10:00:00"
              }]}}},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        502: {"model": schemas.Problem, "description": "Upstream reservation service error",
              "content": {"application/json": {"example": {
                  "type": "about:blank", "title": "Reservation service error: 503 Service Unavailable",
                  "status": 502, "instance": "/employees/1/reservations"
              }}}},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
async def get_reservations(
    employee_id: int = Path(..., description="Employee ID", example=1),
    db: Session = Depends(get_db),
):
    """
    Proxy call to the Reservation service. Requires RESERVATION_SERVICE_URL in the environment.
    """
    emp = crud.get_employee(db, employee_id)
    if not emp or not emp.active:
        raise HTTPException(status_code=404, detail="Employee not found")
    client = ReservationServiceClient()
    try:
        return await client.get_reservations_for_employee(employee_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Reservation service error: {e}")

@router.get(
    "/{employee_id}/context",
    response_model=schemas.EmployeeContextOut,
    summary="Employee context (company, location, business hours from Company Service)",
    responses={
        200: {"description": "Merged view resolved from Company Service (if configured)",
              "content": {"application/json": {"example": {
                  "employeeId": 1,
                  "company": {"id": 1, "name": "Barber Shop", "email": "info@barber.si", "phone": "+38640111222"},
                  "location": {"id": 12, "street": "Trg Leona", "number": "3", "parentLocationId": 1},
                  "businessHours": [
                      {"dayNumber": 1, "day": "MONDAY", "fromTime": "09:00:00", "toTime": "17:00:00"}
                  ]
              }}}},
        404: {"model": schemas.Problem, "description": "Employee not found"},
    },
)
def employee_context(
    employee_id: int = Path(..., description="Employee ID", example=1),
    db: Session = Depends(get_db),
):
    emp = crud.get_employee(db, employee_id)
    if not emp or not emp.active:
        raise HTTPException(status_code=404, detail="Employee not found")

    c = CompanyServiceClient()
    company: Optional[schemas.CompanyRef] = None
    location: Optional[schemas.LocationRef] = None
    business_hours: Optional[List[schemas.BusinessHoursDay]] = None

    if c.enabled() and emp.company_id:
        comp = c.get_company(emp.company_id)
        if comp:
            company = schemas.CompanyRef(
                id=int(comp.get("id")),
                name=comp.get("companyName") or comp.get("name"),
                email=comp.get("email"),
                phone=comp.get("phoneNumber"),
            )
            # weekly BH (requires /business-hours/company/{id} exposed in Company svc)
            bh = c.get_business_hours_by_company(emp.company_id)
            if bh:
                business_hours = [
                    schemas.BusinessHoursDay(
                        dayNumber=int(x.get("dayNumber")),
                        day=str(x.get("day")),
                        fromTime=str(x.get("timeFrom")),
                        toTime=str(x.get("timeTo")),
                        pauseFrom=x.get("pauseFrom"),
                        pauseTo=x.get("pauseTo"),
                    )
                    for x in bh
                ]

    if c.enabled() and emp.location_id:
        loc = c.get_location(emp.location_id)
        if loc:
            # note: your DTO uses "name" that maps to model.street
            location = schemas.LocationRef(
                id=int(loc.get("id")),
                street=loc.get("street") or loc.get("name"),
                number=loc.get("number"),
                parentLocationId=(loc.get("parentLocation", {}) or {}).get("id"),
            )

    return schemas.EmployeeContextOut(
        employeeId=employee_id,
        company=company,
        location=location,
        businessHours=business_hours,
    )
