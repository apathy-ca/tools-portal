import multiprocessing

# Gunicorn config variables
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
threads = 2

# Listening
bind = "0.0.0.0:5000"

# Timeouts
timeout = 120
keepalive = 5

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Use stdout/stderr for logging instead of files
accesslog = "-"
errorlog = "-"
