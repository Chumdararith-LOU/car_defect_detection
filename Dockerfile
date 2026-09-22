FROM python:3.10-slim

# System dependencies required by OpenCV and Git LFS
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Initialize Git LFS globally (so LFS pointer files resolve correctly if cloned inside the container)
RUN git lfs install

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and configuration
COPY app/ ./app/
COPY configs/ ./configs/
COPY models/manifest.json ./models/manifest.json

# Create storage directories (mounted at runtime via docker-compose)
RUN mkdir -p /app/storage/crops /app/storage/jobs

EXPOSE 8000

# Run the FastAPI application via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
