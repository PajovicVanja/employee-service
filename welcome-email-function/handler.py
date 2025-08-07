# welcome-email-function/handler.py
import json
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, EmailStr

class Payload(BaseModel):
    email: EmailStr
    name: str

app = FastAPI()

@app.post("/")
async def send_welcome(request: Request):
    # parse + validate JSON body
    try:
        body = await request.json()
        data = Payload(**body)
    except Exception as e:
        raise HTTPException(400, f"Invalid payload: {e}")

    # your “real” email-sending logic goes here…
    print(f"DEBUG: Sending welcome email to {data.name} <{data.email}>")

    return {"message": f"Welcome email sent to {data.email}"}
