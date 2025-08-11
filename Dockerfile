# DNS By Eye - DNS Delegation Visualizer v1.0.0
# Use a lightweight Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies for graphviz
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt config.py gunicorn_config.py ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

# Create necessary directories and set permissions
RUN mkdir -p /var/log/gunicorn && \
    mkdir -p /app/logs && \
    useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app /var/log/gunicorn && \
    chmod -R 755 /app/app/static && \
    mkdir -p /app/app/static/generated && \
    chown -R appuser:appuser /app/app/static/generated && \
    chmod -R 775 /app/app/static/generated

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app/main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV PYTHONUNBUFFERED=1
ENV GUNICORN_CMD_ARGS="--config=gunicorn_config.py --capture-output --enable-stdio-inheritance"

# Switch to non-root user
USER appuser

# Run the app with proper logging configuration
CMD ["gunicorn", "--config=gunicorn_config.py", "app.main:app"]
