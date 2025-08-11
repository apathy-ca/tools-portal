import multiprocessing
import os

# Gunicorn config variables
loglevel = "info"
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
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

def on_starting(server):
    # Ensure log directory exists
    os.makedirs("/var/log/gunicorn", exist_ok=True)

def worker_abort(worker):
    worker.log.critical("Worker received SIGABRT signal")
