# Stage 1: build wheels
FROM python:3.11-alpine AS builder

# build dependencies (including Rust toolchain, OpenSSL and libffi headers)
RUN apk add --no-cache \
      build-base \
      libffi-dev \
      openssl-dev \
      pkgconfig \
      rust \
      cargo

WORKDIR /app

# copy and build all wheels into /wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: runtime
FROM python:3.11-alpine

# runtime dependencies for cryptography and other C-extensions
RUN apk add --no-cache \
      libstdc++ \
      libffi \
      openssl

WORKDIR /app

# bring in wheels and requirements
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# install from wheels only
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt

# copy application code
COPY . .

# expose your port
EXPOSE 8000

# start the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
