# thumbnail-function/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py app/ ./
EXPOSE 8000

CMD ["uvicorn", "handler:app", "--host", "0.0.0.0", "--port", "$PORT"]
