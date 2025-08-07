# thumbnail-function/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# your handler + storage code
COPY handler.py app/ ./

EXPOSE 8000
# allow Render’s $PORT env var (fallback to 8000 locally)
CMD ["sh", "-c", "uvicorn handler:app --host 0.0.0.0 --port ${PORT:-8000}"]
