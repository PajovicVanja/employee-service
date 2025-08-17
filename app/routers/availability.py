from datetime import time as dtime
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from typing import List, Set

from app import crud, schemas, models
from app.dependencies import get_db
from app.services.company_client import CompanyServiceClient
from app.services.faas_client import FaaSClient

router = APIRouter()


def _overlaps(a_from: dtime, a_to: dtime, b_from: dtime, b_to: dtime) -> bool:
    """
    Returns True iff [a_from, a_to) overlaps [b_from, b_to).
    Touching at the boundary (e.g. 12:00-13:00 and 13:00-14:00) is allowed.
    """
    return a_from < b_to and a_to > b_from


def _validate_no_overlaps(db: Session, employee_id: int, slots: List[schemas.AvailabilitySlotCreate]) -> None:
    """
    Raises HTTPException(400) if any incoming slot:
      - has invalid time range (time_from >= time_to), or
      - overlaps with another incoming slot on the same day, or
      - overlaps with an already saved slot for this employee on the same day.
    """
    if not slots:
        return

    # Basic per-slot sanity
    for s in slots:
        if s.time_from >= s.time_to:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid time range: {s.time_from} .. {s.time_to} (time_from must be < time_to)"
            )

    # Load existing only for the days we are touching
    days_touched: Set[int] = {int(s.day_of_week) for s in slots}
    existing: List[models.AvailabilitySlot] = (
        db.query(models.AvailabilitySlot)
        .filter(
            models.AvailabilitySlot.employee_id == employee_id,
            models.AvailabilitySlot.day_of_week.in_(days_touched),
        )
        .all()
    )

    # Check incoming vs existing
    existing_by_day = {}
    for e in existing:
        existing_by_day.setdefault(int(e.day_of_week), []).append(e)

    for s in slots:
        for e in existing_by_day.get(int(s.day_of_week), []):
            if _overlaps(s.time_from, s.time_to, e.time_from, e.time_to):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Overlapping with existing slot: "
                        f"day={s.day_of_week} new={s.time_from}-{s.time_to} "
                        f"existing(id={e.id})={e.time_from}-{e.time_to}"
                    ),
                )

    # Check incoming vs incoming (within the same request)
    seen_by_day = {}
    for s in slots:
        day = int(s.day_of_week)
        for prev in seen_by_day.get(day, []):
            if _overlaps(s.time_from, s.time_to, prev.time_from, prev.time_to):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Overlapping slots in request payload: "
                        f"day={day} {prev.time_from}-{prev.time_to} vs {s.time_from}-{s.time_to}"
                    ),
                )
        seen_by_day.setdefault(day, []).append(s)


@router.get(
    "/",
    response_model=List[schemas.AvailabilitySlotOut],
    summary="List availability slots",
    responses={
        200: {"description": "Availability slots for employee",
              "content": {"application/json": {"example": [{
                  "id": 10, "day_of_week": 1, "time_from": "09:00:00", "time_to": "12:00:00", "location_id": 3
              }]}}},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def list_availability(
    employee_id: int = Path(..., description="Employee ID", example=1),
    db: Session = Depends(get_db)
):
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return crud.get_availability(db, employee_id)


@router.post(
    "/",
    response_model=List[schemas.AvailabilitySlotOut],
    summary="Add availability slots",
    responses={
        200: {"description": "Slots created",
              "content": {"application/json": {"example": [
                  {"id": 10, "day_of_week": 1, "time_from": "09:00:00", "time_to": "12:00:00", "location_id": 3},
                  {"id": 11, "day_of_week": 3, "time_from": "13:00:00", "time_to": "17:00:00", "location_id": 3}
              ]}}},
        400: {"model": schemas.Problem, "description": "Validation error (overlap, out-of-bounds, bad location)",
              "content": {"application/json": {"example": {
                  "type": "about:blank", "title": "Validation error", "status": 400,
                  "detail": "availability validation failed: overlaps=1, outOfBounds=0",
                  "instance": "/employees/1/availability/"
              }}}},
        404: {"model": schemas.Problem, "description": "Employee not found"},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def add_availability(
    employee_id: int = Path(..., description="Employee ID", example=1),
    slots: List[schemas.AvailabilitySlotCreate] = Body(
        ...,
        description="One or more weekly availability slots",
        examples={
            "twoSlots": {
                "summary": "Two slots in one request",
                "value": [
                    {"day_of_week": 1, "time_from": "09:00:00", "time_to": "12:00:00", "location_id": 3},
                    {"day_of_week": 3, "time_from": "13:00:00", "time_to": "17:00:00", "location_id": 3}
                ],
            }
        },
    ),
    db: Session = Depends(get_db),
):
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Always enforce no-overlap server-side (independent of FAAS).
    _validate_no_overlaps(db, employee_id, slots)

    # Validate locations if Company service is configured
    c = CompanyServiceClient()
    if c.enabled():
        loc_ids: Set[int] = {int(s.location_id) for s in slots if s.location_id is not None}
        for lid in loc_ids:
            if not c.validate_location(lid):
                raise HTTPException(status_code=400, detail=f"location_id {lid} not found")

    # Optional: pre-validate with FAAS (overlaps + business-hours bounds)
    faas = FaaSClient()
    if faas.enabled():
        emp = crud.get_employee(db, employee_id)
        bh = None
        if c.enabled() and emp and emp.company_id:
            # Company service BH keys may be timeFrom/timeTo; client adapts either.
            bh = c.get_business_hours_by_company(emp.company_id)

        check = faas.availability_check(
            slots=[s.model_dump() for s in slots],
            business_hours=bh
        )
        if not check.get("ok", True):
            overlaps = check.get("overlaps", [])
            oob = check.get("outOfBounds", [])
            raise HTTPException(
                status_code=400,
                detail=f"availability validation failed: overlaps={len(overlaps)}, outOfBounds={len(oob)}"
            )

    created = crud.create_availability(db, employee_id, slots)

    # Best-effort audit
    faas.audit("availability.created", entity_id=employee_id, meta={"count": len(created)})

    return created


@router.delete(
    "/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an availability slot",
    responses={
        204: {"description": "Slot deleted"},
        404: {"model": schemas.Problem, "description": "Employee or slot not found",
              "content": {"application/json": {"examples": {
                  "employeeMissing": {"summary": "Unknown employee", "value": {
                      "type": "about:blank", "title": "Employee not found", "status": 404,
                      "instance": "/employees/999/availability/10"
                  }},
                  "slotMissing": {"summary": "Unknown slot", "value": {
                      "type": "about:blank", "title": "Slot not found", "status": 404,
                      "instance": "/employees/1/availability/999"
                  }},
              }}}},
        500: {"model": schemas.Problem, "description": "Server error"},
    },
)
def remove_availability(
    employee_id: int = Path(..., description="Employee ID", example=1),
    slot_id: int = Path(..., description="Availability slot ID", example=10),
    db: Session = Depends(get_db),
):
    if not crud.get_employee(db, employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    slot = crud.delete_availability_slot(db, slot_id)
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

    FaaSClient().audit("availability.deleted", entity_id=employee_id, meta={"slot_id": slot_id})
