# tests/conftest.py

import os
import sys

# ensure our project root (the directory containing `app/`) is on the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 1) make sure we use sqlite:///:memory: for everything
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL

# 2) create a single-connection engine with StaticPool + disable thread check
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

# 3) patch the real app.database to use our test engine/session
import app.database
app.database.engine = engine
app.database.SessionLocal = TestingSessionLocal

# 4) now import Base, FastAPI app, etc.
from fastapi.testclient import TestClient
from app.database import Base
from app.dependencies import get_db
from app.main import app

# 5) create all tables once on our test engine
Base.metadata.create_all(bind=engine)

# 6) override the FastAPI get_db dependency for REST routes
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
