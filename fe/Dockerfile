# fe/Dockerfile
# Stage 1: Build dependencies
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .

# We only need streamlit and requests for FE really, but using the same requirements is fine.
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential \
    && pip install --user --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Runtime
FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY fe /app/fe
COPY .env* /app/

EXPOSE 8501

CMD ["streamlit", "run", "fe/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
