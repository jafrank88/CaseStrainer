FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN ls -l /app

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
RUN pip --version && pip install --no-cache-dir -r requirements.txt --verbose
RUN rm -f requirements.txt

# Now copy the rest of the code as app user
COPY --chown=app:app . .

# Switch to app user and install Python dependencies
RUN pip --version && pip install --no-cache-dir -r requirements.txt --verbose
RUN rm -f requirements.txt

# Create necessary directories as root
RUN mkdir -p /home/app/data /home/app/logs /home/app/uploads /home/app/temp_uploads /app/citation_cache && \
    chown -R app:app /home/app /app/citation_cache

# Switch to non-root user for running the app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/casestrainer/api/health || exit 1

# Set the default command
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]