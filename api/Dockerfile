# api/Dockerfile
# Stage 1: Build dependencies
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential \
    && pip install --upgrade pip \
    && pip install --user --no-cache-dir --retries 5 --default-timeout=1200 -r requirements.txt \
    && apt-get purge -y --auto-remove gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Runtime
FROM python:3.10-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy app code
COPY api /app/api
COPY agent /app/agent
COPY ingestion /app/ingestion
COPY .env* /app/

EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
