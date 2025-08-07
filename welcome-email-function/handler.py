import json
import os
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, EmailStr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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

    # construct SendGrid message
    message = Mail(
        from_email="no-reply@yourdomain.com",
        to_emails=data.email,
        subject="🎉 Welcome aboard!",
        html_content=(
            f"<strong>Hi {data.name},</strong><br>"
            "Thanks for joining us—let’s get started!"
        )
    )

    # send it
    try:
        sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
        response = sg.send(message)
    except Exception as e:
        raise HTTPException(500, f"Failed to send email: {e}")

    return {"message": f"Welcome email sent to {data.email}", "sg_status": response.status_code}
