from datetime import date, time, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, constr, ConfigDict

# ───────────────────────── Common error schema ─────────────────────────

class Problem(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "type": "about:blank",
            "title": "Not Found",
            "status": 404,
            "detail": "Employee not found",
            "instance": "/employees/999"
        }
    })
    type: Optional[str] = "about:blank"
    title: str
    status: int
    detail: Optional[str] = None
    instance: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

# ───────────────────────── Availability ─────────────────────────

class AvailabilitySlotBase(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "day_of_week": 1,
            "time_from": "09:00:00",
            "time_to": "17:00:00",
            "location_id": 3
        }
    })
    day_of_week: int
    time_from: time
    time_to: time
    location_id: Optional[int] = None

class AvailabilitySlotCreate(AvailabilitySlotBase):
    pass

class AvailabilitySlotOut(AvailabilitySlotBase):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 42,
            "day_of_week": 1,
            "time_from": "09:00:00",
            "time_to": "17:00:00",
            "location_id": 3
        }
    })
    id: int

# ───────────────────────── Skills ─────────────────────────

class EmployeeSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {"service_id": 7}
    })
    service_id: int

# ───────────────────────── Employee ─────────────────────────

class EmployeeBase(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "idp_id": "auth0|abc123",
            "first_name": "John",
            "last_name": "Doe",
            "gender": True,
            "birth_date": "1990-01-01",
            "id_picture": "/files/thumbnails/1.jpg"
        }
    })
    idp_id: Optional[str] = None
    first_name: constr(min_length=1)
    last_name: constr(min_length=1)
    gender: bool
    birth_date: date
    id_picture: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(EmployeeBase):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "idp_id": None,
            "first_name": "Jane",
            "last_name": "Doe",
            "gender": False,
            "birth_date": "1992-02-02",
            "id_picture": None,
            "active": True
        }
    })
    active: bool

class EmployeeOut(EmployeeBase):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 1,
            "idp_id": "auth0|abc123",
            "first_name": "John",
            "last_name": "Doe",
            "gender": True,
            "birth_date": "1990-01-01",
            "id_picture": "/files/thumbnails/1.jpg",
            "active": True,
            "availability": [
                {
                    "id": 10,
                    "day_of_week": 1,
                    "time_from": "09:00:00",
                    "time_to": "17:00:00",
                    "location_id": 3
                }
            ],
            "skills": [{"service_id": 7}]
        }
    })
    id: int
    active: bool
    availability: List[AvailabilitySlotOut] = []
    skills: List[EmployeeSkillOut] = []

# ───────────────────────── Inter-service DTO ─────────────────────────

class Reservation(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 555,
            "employee_id": 1,
            "date": "2025-01-01",
            "time_from": "09:00:00",
            "time_to": "10:00:00"
        }
    })
    id: int
    employee_id: int
    date: date
    time_from: time
    time_to: time
