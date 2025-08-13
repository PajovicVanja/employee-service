from sqlalchemy.orm import Session
from typing import List
from app import models, schemas

# Employee
def get_employee(db: Session, employee_id: int):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Employee)
        .filter(models.Employee.active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_employee(db: Session, emp: schemas.EmployeeCreate):
    # pydantic v2: model_dump()
    db_emp = models.Employee(**emp.model_dump())
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    return db_emp

def update_employee(db: Session, employee_id: int, emp: schemas.EmployeeUpdate):
    db_emp = get_employee(db, employee_id)
    if not db_emp:
        return None
    for field, value in emp.model_dump().items():
        setattr(db_emp, field, value)
    db.commit()
    db.refresh(db_emp)
    return db_emp

def soft_delete_employee(db: Session, employee_id: int):
    db_emp = get_employee(db, employee_id)
    if db_emp:
        db_emp.active = False
        db.commit()
    return db_emp

# Availability
def get_availability(db: Session, employee_id: int):
    return db.query(models.AvailabilitySlot).filter(models.AvailabilitySlot.employee_id == employee_id).all()

def create_availability(db: Session, employee_id: int, slots: List[schemas.AvailabilitySlotCreate]):
    objs = []
    for slot in slots:
        obj = models.AvailabilitySlot(employee_id=employee_id, **slot.model_dump())
        db.add(obj)
        objs.append(obj)
    db.commit()
    return objs

def delete_availability_slot(db: Session, slot_id: int):
    obj = db.query(models.AvailabilitySlot).filter(models.AvailabilitySlot.id == slot_id).first()
    if obj:
        db.delete(obj)
        db.commit()
    return obj

# Skills
def get_skills(db: Session, employee_id: int):
    return db.query(models.EmployeeSkill).filter(models.EmployeeSkill.employee_id == employee_id).all()

def replace_skills(db: Session, employee_id: int, service_ids: List[int]):
    db.query(models.EmployeeSkill).filter(models.EmployeeSkill.employee_id == employee_id).delete()
    for sid in service_ids:
        db.add(models.EmployeeSkill(employee_id=employee_id, service_id=sid))
    db.commit()
    return get_skills(db, employee_id)
