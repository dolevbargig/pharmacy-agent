# Multi-stage Dockerfile for Pharmacy AI Agent

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application code (no frontend - served by nginx)
COPY backend/ /app/backend/
COPY database/ /app/database/

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Health check (using urllib which is built-in Python)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:8000/health', timeout=5)"

# Create entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Run the application via entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
