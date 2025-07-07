FROM python:3.11-slim

WORKDIR /app

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
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd --create-home --shell /bin/bash app

# Copy requirements file and install dependencies as root
COPY requirements.txt .
RUN pip --version && pip install --no-cache-dir -r requirements.txt --verbose
RUN rm -f requirements.txt

# Create necessary directories with proper permissions as root
RUN mkdir -p /home/app/data /home/app/logs /home/app/uploads /home/app/temp_uploads /app/citation_cache
RUN chown -R app:app /app /home/app

# Switch to non-root user for running the app
USER app

# Copy application code
COPY src ./src
COPY config.json .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/casestrainer/api/health || exit 1

CMD ["python", "src/app_final_vue.py"]
