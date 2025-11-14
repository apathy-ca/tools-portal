"""
Tools Portal v2 - Configuration
Simplified single-source configuration.
"""
import os
import warnings


class Config:
    """Application configuration."""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())

    # Security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

    # Application
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    TESTING = os.environ.get('TESTING', 'false').lower() == 'true'
    VERSION = '2.0.0'

    # Request limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Cache settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # Redis (optional)
    REDIS_URL = os.environ.get('REDIS_URL')

    # Database (optional - for future use)
    DATABASE_URL = os.environ.get('DATABASE_URL')

    # Warn if SECRET_KEY is auto-generated
    if not os.environ.get('SECRET_KEY'):
        warnings.warn(
            "SECRET_KEY not set - using generated key. "
            "Sessions will reset on restart. Set SECRET_KEY in production.",
            UserWarning
        )
