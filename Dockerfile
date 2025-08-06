# DNS By Eye - DNS Delegation Visualizer v1.0.0
# Use a lightweight Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies for graphviz
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt config.py .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

# Create non-root user and set ownership
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser /app && \
    chmod -R 755 /app/app/static && \
    mkdir -p /app/app/static/generated && \
    chown -R appuser:appuser /app/app/static/generated && \
    chmod -R 775 /app/app/static/generated

# Expose Flask port
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=app/main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Switch to non-root user
USER appuser

# Run the app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:app"]
