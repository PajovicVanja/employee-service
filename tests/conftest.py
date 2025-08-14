# tests/conftest.py

import os
import sys
import tempfile

# ensure our project root (the directory containing `app/`) is on the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Isolated on-disk storage for StaticFiles mount & thumbnails
_tmp_storage = tempfile.mkdtemp(prefix="emp_storage_")
os.environ["STORAGE_PATH"] = _tmp_storage

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL

# If your interop client gets instantiated, make sure base URL exists
os.environ.setdefault("RESERVATION_SERVICE_URL", "http://dummy-reservation-service.local/api")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

# Patch app.database to use our test engine/session
import app.database
app.database.engine = engine
app.database.SessionLocal = TestingSessionLocal

# Now import Base, FastAPI app, etc.
from fastapi.testclient import TestClient
from app.database import Base
from app.dependencies import get_db
from app.main import app

# Create schema
Base.metadata.create_all(bind=engine)

# Override dependency for routes
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
