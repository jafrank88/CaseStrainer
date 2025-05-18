FROM python:3.8-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-dev \
    python3-pip \
    python3-wheel \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies with error handling
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p uploads static templates

# Copy the rest of the application
COPY . .

# Copy Vue.js frontend build files
COPY casestrainer-vue/dist/ static/

# Set environment variables
ENV FLASK_APP=src/app_final_vue.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "src/app_final_vue.py", "--host", "0.0.0.0", "--port", "5000", "--use-waitress"]