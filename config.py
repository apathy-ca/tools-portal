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
    
    # Logging configuration
    LOG_FILE = 'tools_portal.log'
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 5
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Version info
    VERSION = '2.0.1-ai'
    
    # Optional AI Integration Configuration
    # These settings are only used if Symposium backend is available
    SYMPOSIUM_BACKEND_URL = os.environ.get('SYMPOSIUM_BACKEND_URL', 'http://localhost:8000')
    SYMPOSIUM_AUTH_TOKEN = os.environ.get('SYMPOSIUM_AUTH_TOKEN', 'dev-token')
    SYMPOSIUM_REQUEST_TIMEOUT = int(os.environ.get('SYMPOSIUM_REQUEST_TIMEOUT', '30'))
    
    # AI Chat Configuration (optional - defaults work fine)
    AI_CHAT_MAX_MESSAGE_LENGTH = int(os.environ.get('AI_CHAT_MAX_MESSAGE_LENGTH', '2000'))
    AI_CHAT_MAX_FILE_SIZE = int(os.environ.get('AI_CHAT_MAX_FILE_SIZE', '10485760'))  # 10MB
    AI_CHAT_ALLOWED_FILE_TYPES = os.environ.get(
        'AI_CHAT_ALLOWED_FILE_TYPES',
        '.txt,.pdf,.docx,.md,.json,.csv,.py,.js,.html,.css,.log'
    ).split(',')
    
    # Feature toggles (optional)
    ENABLE_FILE_UPLOAD = os.environ.get('ENABLE_FILE_UPLOAD', 'true').lower() == 'true'
    ENABLE_SAGE_SELECTION = os.environ.get('ENABLE_SAGE_SELECTION', 'true').lower() == 'true'
    ENABLE_MODEL_SELECTION = os.environ.get('ENABLE_MODEL_SELECTION', 'true').lower() == 'true'
    
    # Rate limiting (optional - disabled by default)
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'false').lower() == 'true'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per hour')
    
    # CORS configuration (optional - disabled by default)
    CORS_ENABLED = os.environ.get('CORS_ENABLED', 'false').lower() == 'true'
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    
    # Redis Configuration
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
    REDIS_DB = int(os.environ.get('REDIS_DB', '1'))  # Use database 1 for tools-portal
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    
    @property
    def REDIS_URL(self):
        """Get Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
