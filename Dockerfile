FROM python:3.11-slim

# Install system dependencies including hyperscan and Python build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libhyperscan-dev \
    python3-setuptools \
    python3-pip \
    python3-wheel \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=src/app_final_vue.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "src/app_final_vue.py", "--host", "0.0.0.0", "--port", "5000"] 