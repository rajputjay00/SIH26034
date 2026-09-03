# ==============================================================================
# NIRIKSHAN / SIH26034 — FastAPI Backend Container Dockerfile
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=".:backend" \
    PORT=8000

WORKDIR /app

# Install system runtime dependencies for OpenCV and ONNX
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend application code
COPY backend /app/backend

# Create persistent runtime storage directories
RUN mkdir -p /app/storage/evidence /app/storage/derived /app/storage/reports

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# Launch production server with dynamic port
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
