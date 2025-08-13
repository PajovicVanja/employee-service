import os
import time
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

# load .env
load_dotenv()

from app.database import engine, Base
import app.models  # noqa: ensure models are registered

# routers
from app.routers import employees, availability, skills

# graphql
from strawberry.asgi import GraphQL
from app.graphql.schema import schema

app = FastAPI(
    title="Employee Service",
    description="Manages employees, availability slots and skills. Auth is handled upstream by the API Gateway.",
    version="1.1.0",
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

@app.on_event("startup")
def on_startup():
    # wait for DB
    for _ in range(10):
        try:
            with engine.connect():
                break
        except OperationalError:
            time.sleep(2)
    Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["health"], summary="Health check")
def health():
    return {"status": "ok"}

# GraphQL (no auth here; API Gateway should guard it if needed)
graphql_app = GraphQL(schema)
app.mount("/graphql", graphql_app, name="graphql")

# REST (no in-service auth; API Gateway in front)
app.include_router(
    employees.router,
    prefix="/employees",
    tags=["employees"],
)
app.include_router(
    availability.router,
    prefix="/employees/{employee_id}/availability",
    tags=["availability"],
)
app.include_router(
    skills.router,
    prefix="/employees/{employee_id}/skills",
    tags=["skills"],
)
