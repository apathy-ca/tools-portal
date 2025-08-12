# Multi-stage build for Tools Portal
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Copy portal requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy portal application
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Build DNS By Eye tool
FROM base as dns-by-eye-builder
WORKDIR /app/tools/dns-by-eye
COPY tools/dns-by-eye/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM base as final
WORKDIR /app

# Copy DNS By Eye tool
COPY --from=dns-by-eye-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY tools/ tools/

# Create directories for generated files
RUN mkdir -p tools/dns-by-eye/app/static/generated

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "app.py"]
