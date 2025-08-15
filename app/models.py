# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    idp_id = Column(String(255), unique=True, nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    gender = Column(Boolean, nullable=False)
    birth_date = Column(DateTime, nullable=False)
    id_picture = Column(String(255), nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    # ─── Integration fields ──────────────────────────────────────────────────
    company_id = Column(Integer, nullable=True)      # FK to Company (remote)
    location_id = Column(Integer, nullable=True)     # home branch (remote)

    availability = relationship(
        "AvailabilitySlot",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    skills = relationship(
        "EmployeeSkill",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    time_from = Column(Time, nullable=False)
    time_to = Column(Time, nullable=False)
    location_id = Column(Integer, nullable=True)  # Location from Company svc

    employee = relationship("Employee", back_populates="availability")

class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    employee_id = Column(Integer, ForeignKey("employee.id"), primary_key=True)
    service_id = Column(Integer, primary_key=True)  # ServiceM.id from Company svc

    employee = relationship("Employee", back_populates="skills")
