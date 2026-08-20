FROM python:3.10-slim

# Set system environment variables to optimize Python inside Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the operational working directory inside the container
WORKDIR /app

# Install critical system-level dependencies for OpenCV and Git tracking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements manifest first to maximize Docker layer caching
COPY requirements.txt /app/

# Upgrade pip and install all core Python libraries natively
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the remaining project directories into the deployment application space
COPY src/ /app/src/
COPY configs/ /app/configs/
COPY Makefile /app/

# Expose port 5000 for standard out-of-container MLflow communications
EXPOSE 5000

# Set a safe default shell command execution entry point
CMD ["bash"]
