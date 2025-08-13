import os

class Config:
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

    # Application settings
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    TESTING = os.environ.get('TESTING', 'false').lower() == 'true'
    
    # Request size limits
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB
    
    # DNS settings
    DNS_TIMEOUT = float(os.environ.get('DNS_TIMEOUT', '5.0'))
    DNS_LIFETIME = float(os.environ.get('DNS_LIFETIME', '10.0'))
    
    # Logging configuration
    LOG_FILE = 'ipwhale.log'
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 5
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Version info
    VERSION = '1.0.0'
