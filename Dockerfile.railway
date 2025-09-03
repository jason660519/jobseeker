# Railway-optimized Dockerfile for JobSpy Flask Application
# Simple single-stage build specifically designed for Railway deployment

FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
COPY web_app/requirements.txt ./web_app_requirements.txt

# Install Python dependencies
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install -r requirements.txt && \
    pip3 install -r web_app_requirements.txt

# Copy application code
COPY . .

# Install jobseeker package in development mode
RUN pip3 install -e .

# Change to web_app directory
WORKDIR /app/web_app

# Expose port (Railway will set $PORT)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start command optimized for Railway
CMD python3 -m gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -