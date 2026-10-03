# Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 100 -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user
RUN useradd --create-home appuser
USER appuser

# Expose port
EXPOSE 8000

# Apply pending migrations (bootstrap.py), then start the API. `exec` keeps
# uvicorn as PID 1 so it receives SIGTERM and can shut down gracefully.
CMD ["sh", "-c", "python bootstrap.py && exec uvicorn main:app --host 0.0.0.0 --port 8000"]

# Liveness probe (no curl in the slim image, so use the stdlib).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1