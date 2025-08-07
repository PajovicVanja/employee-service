# serverless/send_welcome_email.py
import json

def handler(event, context):
    body = json.loads(event.get("body", "{}"))
    email = body.get("email")
    name  = body.get("name")
    # Insert real email logic here...
    print(f"DEBUG: Sending welcome email to {name} <{email}>")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Welcome email sent to {email}"})
    }
