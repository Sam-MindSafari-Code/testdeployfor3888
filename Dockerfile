# syntax=docker/dockerfile:1
# FastAPI + Uvicorn app with Postgres (psycopg2) support
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System packages needed for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Work at the repository root inside the container
WORKDIR /app

# Copy Python dependencies (expects requirements.txt at repo root)
COPY requirements.txt ./requirements.txt

# Install dependencies (requirements.txt should include psycopg2-binary, python-dotenv, python-multipart)
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend ./backend

# Expose app port (informational)
EXPOSE 8000
ENV PORT=8000

# Start the FastAPI app (Vercel/other PaaS will provide $PORT)
WORKDIR /app/backend
CMD ["bash", "-lc", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
