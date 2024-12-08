# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y \
    libmariadb-dev-compat \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file into the container
COPY requirements.txt .

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY . .

# Expose the application's port
EXPOSE 5000

# Use gunicorn to run the app in production
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
