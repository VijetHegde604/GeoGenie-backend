FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# TARGETARCH is automatically set by Docker Buildx for multiplatform builds
# Values: amd64, arm64, arm/v7, etc.
ARG TARGETARCH
ARG TARGETPLATFORM

# Copy both requirements files
COPY requirements.txt requirements-pi.txt ./

# Select requirements file based on architecture
# For ARM64 (Raspberry Pi 5), use requirements-pi.txt
# For AMD64/x86_64, use requirements.txt
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        REQ_FILE=requirements-pi.txt; \
        echo "🔧 Building for ARM64 (Raspberry Pi) - using requirements-pi.txt"; \
    else \
        REQ_FILE=requirements.txt; \
        echo "🔧 Building for AMD64/x86_64 - using requirements.txt"; \
    fi && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r ${REQ_FILE}

# Copy the pre-download script and run it
COPY setup_model.py .
RUN python setup_model.py

# Copy the rest of the app
COPY . .

# Ensure the script is executable
RUN chmod +x /app/entrypoint.sh

# The script runs first, then executes the CMD
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
