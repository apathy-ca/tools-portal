import multiprocessing
import os
import logging

# Gunicorn config variables
loglevel = "info"
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
capture_output = True
enable_stdio_inheritance = True

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

# Logging setup
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': errorlog,
            'formatter': 'standard',
            'mode': 'a+'
        },
    },
    'loggers': {
        'gunicorn.error': {
            'handlers': ['error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

def on_starting(server):
    """
    Initialize logging and ensure directories exist before starting.
    """
    # Ensure log directory exists
    os.makedirs("/var/log/gunicorn", exist_ok=True)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(errorlog),
            logging.StreamHandler()
        ]
    )

def worker_abort(worker):
    """
    Handle worker abort events.
    """
    worker.log.critical("Worker received SIGABRT signal")

def post_worker_init(worker):
    """
    Set up worker-specific logging after initialization.
    """
    worker.log.info(f"Worker {worker.pid} initialized")

def worker_exit(server, worker):
    """
    Handle worker exit events.
    """
    worker.log.info(f"Worker {worker.pid} exiting")
