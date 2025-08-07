# app/graphql/schema.py
import strawberry
from datetime import datetime
from typing import List, Optional

from app.database import SessionLocal
from app.models import Employee as EmployeeModel, AvailabilitySlot as AvailabilityModel, EmployeeSkill as SkillModel

@strawberry.scalar(description="ISO-formatted DateTime")
def DateTime(value: datetime) -> str:
    return value.isoformat()

@strawberry.type
class AvailabilitySlot:
    id: int
    day_of_week: int
    time_from: str
    time_to: str
    location_id: Optional[int]

@strawberry.type
class Skill:
    service_id: int

@strawberry.type
class Employee:
    id: int
    first_name: str
    last_name: str
    gender: bool
    birth_date: DateTime
    active: bool

    @strawberry.field
    def availability(self) -> List[AvailabilitySlot]:
        db = SessionLocal()
        slots = db.query(AvailabilityModel).filter(AvailabilityModel.employee_id == self.id).all()
        return [
            AvailabilitySlot(
                id=s.id,
                day_of_week=s.day_of_week,
                time_from=s.time_from.isoformat(),
                time_to=s.time_to.isoformat(),
                location_id=s.location_id,
            )
            for s in slots
        ]

    @strawberry.field
    def skills(self) -> List[Skill]:
        db = SessionLocal()
        skills = db.query(SkillModel).filter(SkillModel.employee_id == self.id).all()
        return [Skill(service_id=sk.service_id) for sk in skills]

@strawberry.type
class Query:
    @strawberry.field
    def employees(self) -> List[Employee]:
        db = SessionLocal()
        emps = db.query(EmployeeModel).filter(EmployeeModel.active == True).all()
        return [
            Employee(
                id=e.id,
                first_name=e.first_name,
                last_name=e.last_name,
                gender=e.gender,
                birth_date=e.birth_date,
                active=e.active,
            )
            for e in emps
        ]

    @strawberry.field
    def employee(self, id: int) -> Optional[Employee]:
        db = SessionLocal()
        e = db.query(EmployeeModel).filter(EmployeeModel.id == id).first()
        if not e:
            return None
        return Employee(
            id=e.id,
            first_name=e.first_name,
            last_name=e.last_name,
            gender=e.gender,
            birth_date=e.birth_date,
            active=e.active,
        )

schema = strawberry.Schema(query=Query)
