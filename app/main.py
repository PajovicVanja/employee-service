import os
import time
from typing import Tuple
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

# load .env
load_dotenv()

from app.database import engine, Base
from contextlib import asynccontextmanager
import app.models  # noqa: ensure models are registered

# routers
from app.routers import employees, availability, skills
from app.schemas import Problem

OPENAPI_TAGS = [
    {"name": "employees", "description": "Employee CRUD and media upload."},
    {"name": "availability", "description": "Per-employee weekly availability slots."},
    {"name": "skills", "description": "Per-employee service skills."},
    {"name": "health", "description": "Service health & readiness."},
]

app = FastAPI(
    title="Employee Service",
    description=(
        "Manages employees, availability slots and skills.\n\n"
        "Authentication & authorization are handled by the API Gateway. "
        "This service validates optional company/location/service data via Company Service when configured."
    ),
    version="1.3.0",
    openapi_tags=OPENAPI_TAGS,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve everything under STORAGE_PATH as /files
app.mount(
    "/files",
    StaticFiles(directory=os.getenv("STORAGE_PATH", "storage")),
    name="files",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    for _ in range(10):
        try:
            with engine.connect():
                break
        except OperationalError:
            time.sleep(2)
    Base.metadata.create_all(bind=engine)
    yield  # Application runs here

@app.get("/health", tags=["health"], summary="Health check", responses={
    200: {
        "description": "Service is healthy",
        "content": {"application/json": {"example": {"status": "ok"}}}
    }
})
def health():
    return {"status": "ok"}

# ───────────────────── Global exception mappers ─────────────────────

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    problem = Problem(
        title="Internal Server Error",
        status=500,
        detail=str(exc) if os.getenv("ENV", "dev") == "dev" else "Unexpected error",
        instance=request.url.path
    )
    return JSONResponse(status_code=500, content=problem.model_dump())

from fastapi import HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    problem = Problem(
        title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
        status=exc.status_code,
        instance=request.url.path
    )
    return JSONResponse(status_code=exc.status_code, content=problem.model_dump())

# ─────────────────────────── REST routers ───────────────────────────

app.include_router(employees.router, prefix="/employees", tags=["employees"])
app.include_router(availability.router, prefix="/employees/{employee_id}/availability", tags=["availability"])
app.include_router(skills.router, prefix="/employees/{employee_id}/skills", tags=["skills"])
