# app/routers/auth.py
import os
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas import Token

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ISSUER = os.getenv("JWT_ISSUER")

# In-memory demo users
fake_users = {
    "alice": {"username": "alice", "full_name": "Alice Wonderland", "role": "admin", "password": "secret1"},
    "bob":   {"username": "bob",   "full_name": "Bob Builder",     "role": "user",  "password": "secret2"},
}

router = APIRouter()

@router.post(
    "/token",
    response_model=Token,
    summary="Generate JWT access token",
    responses={401: {"description": "Invalid credentials"}}
)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.utcnow()
    to_encode = {
        "sub":  user["username"],
        "name": user["full_name"],
        "role": user["role"],
        "iss":  ISSUER,
        "iat":  now,
        "exp":  now + timedelta(minutes=30),
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
