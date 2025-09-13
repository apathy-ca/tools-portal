import os

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Logging configuration
    LOG_FILE = os.environ.get('LOG_FILE', 'tools-portal.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', '10240'))
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '10'))
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Version info
    VERSION = '2.0.0-ai'
    
    # AI Integration Configuration
    SYMPOSIUM_BACKEND_URL = os.environ.get('SYMPOSIUM_BACKEND_URL', 'http://localhost:8000')
    SYMPOSIUM_AUTH_TOKEN = os.environ.get('SYMPOSIUM_AUTH_TOKEN', 'dev-token')
    
    # AI Chat Configuration
    AI_CHAT_ENABLED = os.environ.get('AI_CHAT_ENABLED', 'true').lower() == 'true'
    AI_CHAT_MAX_MESSAGE_LENGTH = int(os.environ.get('AI_CHAT_MAX_MESSAGE_LENGTH', '2000'))
    AI_CHAT_MAX_FILE_SIZE = int(os.environ.get('AI_CHAT_MAX_FILE_SIZE', '10485760'))  # 10MB
    AI_CHAT_ALLOWED_FILE_TYPES = os.environ.get(
        'AI_CHAT_ALLOWED_FILE_TYPES', 
        '.txt,.pdf,.docx,.md,.json,.csv,.py,.js,.html,.css,.log'
    ).split(',')
    
    # Request timeouts for Symposium backend
    SYMPOSIUM_REQUEST_TIMEOUT = int(os.environ.get('SYMPOSIUM_REQUEST_TIMEOUT', '30'))
    
    # Features toggles
    ENABLE_FILE_UPLOAD = os.environ.get('ENABLE_FILE_UPLOAD', 'true').lower() == 'true'
    ENABLE_SAGE_SELECTION = os.environ.get('ENABLE_SAGE_SELECTION', 'true').lower() == 'true'
    ENABLE_MODEL_SELECTION = os.environ.get('ENABLE_MODEL_SELECTION', 'true').lower() == 'true'
    
    # Rate limiting (if needed in future)
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'false').lower() == 'true'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per hour')
    
    # CORS configuration (if needed for external access)
    CORS_ENABLED = os.environ.get('CORS_ENABLED', 'false').lower() == 'true'
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

class DevelopmentConfig(Config):
    DEBUG = True
    SYMPOSIUM_BACKEND_URL = os.environ.get('SYMPOSIUM_BACKEND_URL', 'http://localhost:8000')
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    SYMPOSIUM_BACKEND_URL = os.environ.get('SYMPOSIUM_BACKEND_URL', 'http://symposium-backend:8000')
    LOG_LEVEL = 'INFO'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-must-be-set'

class TestingConfig(Config):
    TESTING = True
    SYMPOSIUM_BACKEND_URL = 'http://mock-symposium:8000'
    AI_CHAT_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}