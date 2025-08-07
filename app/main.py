# app/main.py
import os
import time

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

# load .env
load_dotenv()

from app.database import engine, Base
from app.auth import verify_jwt_token
import app.models  # noqa

# ── new imports for auth + GraphQL ─────────────────────────────────────────────
from app.routers import auth
import strawberry
from strawberry.asgi import GraphQL
from app.graphql.schema import schema

app = FastAPI(
    title="Employee Service",
    description="Manages employees, availability slots and skills. All endpoints are JWT‐protected.",
    version="1.0.0",
    openapi_tags=[
        {"name": "health",       "description": "Service health check"},
        {"name": "employees",    "description": "Employee CRUD"},
        {"name": "availability", "description": "Manage employee availability slots"},
        {"name": "skills",       "description": "Manage employee skills"},
        {"name": "auth",         "description": "Authentication"},
        {"name": "graphql",      "description": "GraphQL API"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # wait for MySQL to be ready
    for _ in range(10):
        try:
            with engine.connect():
                break
        except OperationalError:
            time.sleep(2)
    # create tables
    Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["health"], summary="Health check")
def health() -> dict:
    return {"status": "ok"}

# ── include auth (unprotected) ────────────────────────────────────────────────
app.include_router(auth.router, tags=["auth"])

# ── mount GraphQL endpoint ───────────────────────────────────────────────────
graphql_app = GraphQL(schema)
app.mount("/graphql", graphql_app, name="graphql")

# ── include your existing REST routers (JWT‐protected) ───────────────────────
from app.routers import employees, availability, skills

app.include_router(
    employees.router,
    prefix="/employees",
    tags=["employees"],
    dependencies=[Depends(verify_jwt_token)],
)
app.include_router(
    availability.router,
    prefix="/employees/{employee_id}/availability",
    tags=["availability"],
    dependencies=[Depends(verify_jwt_token)],
)
app.include_router(
    skills.router,
    prefix="/employees/{employee_id}/skills",
    tags=["skills"],
    dependencies=[Depends(verify_jwt_token)],
)
