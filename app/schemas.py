from datetime import date, time, datetime
from typing import List, Optional
from pydantic import BaseModel, constr

class AvailabilitySlotBase(BaseModel):
    day_of_week: int
    time_from: time
    time_to: time
    location_id: Optional[int]

class AvailabilitySlotCreate(AvailabilitySlotBase):
    pass

class AvailabilitySlotOut(AvailabilitySlotBase):
    id: int
    class Config:
        orm_mode = True

class EmployeeSkillOut(BaseModel):
    service_id: int
    class Config:
        orm_mode = True

class EmployeeBase(BaseModel):
    idp_id: Optional[str] = None
    first_name: constr(min_length=1)
    last_name: constr(min_length=1)
    gender: bool
    birth_date: date
    id_picture: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(EmployeeBase):
    active: bool

class EmployeeOut(EmployeeBase):
    id: int
    active: bool
    availability: List[AvailabilitySlotOut] = []
    skills: List[EmployeeSkillOut] = []
    class Config:
        orm_mode = True

# ── New JWT / inter-service models ─────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: str
    name: str
    role: str
    exp: datetime

class Reservation(BaseModel):
    id: int
    employee_id: int
    date: date
    time_from: time
    time_to: time

    class Config:
        orm_mode = True
