# Use official Python image
FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies first (cache efficient)
COPY requirements.txt requirements.txt
# Install git before pip install
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src/app_final_vue.py
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    curl \
    git \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy only essential source code and config
COPY --chown=app:app src/ /app/src/
COPY --chown=app:app app/ /app/app/
COPY --chown=app:app config/ /app/config/
COPY --chown=app:app templates/ /app/templates/
COPY --chown=app:app static/ /app/static/
COPY --chown=app:app wait-for-redis.py /app/wait-for-redis.py
COPY --chown=app:app VERSION /app/VERSION
# Clean up any .pyc files and __pycache__ directories after copy
RUN find . -type d -name '__pycache__' -exec rm -r {} + && find . -type f -name '*.pyc' -delete

# (Optional) Add build arg and label for cache busting
ARG SOURCE_COMMIT=dev
LABEL source_commit=$SOURCE_COMMIT

# Ensure /app/logs exists and is owned by app user
RUN mkdir -p /app/logs && chown app:app /app/logs

# Create necessary directories as root
RUN mkdir -p /home/app/data /home/app/logs /home/app/uploads /home/app/temp_uploads /app/citation_cache

# Set ownership to app user
RUN chown -R app:app /home/app/data /home/app/logs /home/app/uploads /home/app/temp_uploads /app/citation_cache

# Switch to app user
USER app

# Entrypoint and command are set in docker-compose