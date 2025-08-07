from fastapi import FastAPI, Request
from pydantic import BaseModel

class EmailRequest(BaseModel):
    email: str
    name: str

app = FastAPI()

@app.post("/", status_code=200)
async def handler(req: EmailRequest):
    # insert real email logic here...
    print(f"DEBUG: Sending welcome email to {req.name} <{req.email}>")
    return {"message": f"Welcome email sent to {req.email}"}
