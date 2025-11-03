# -*- coding: utf-8 -*-
"""
Tools Portal - Main Application
A collection of useful network and system administration tools.

Refactored with modular architecture for better maintainability and scalability.
"""

from flask import Flask
from logging.handlers import RotatingFileHandler
import logging

from config import Config
from flask_caching import Cache


def create_app(config_class=Config):
    """
    Application factory pattern.

    Args:
        config_class: Configuration class to use

    Returns:
        Configured Flask application
    """
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(config_class)

    # Initialize extensions
    initialize_extensions(app)

    # Configure logging
    configure_logging(app)

    # Register blueprints
    register_blueprints(app)

    app.logger.info('Tools Portal startup - Modular architecture')

    return app


def initialize_extensions(app):
    """
    Initialize Flask extensions.

    Args:
        app: Flask application instance
    """
    # Initialize caching
    cache = Cache(app, config={
        'CACHE_TYPE': 'simple',  # In-memory cache
        'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default
    })

    # Store cache instance in app for access in routes
    app.cache = cache


def configure_logging(app):
    """
    Configure application logging.

    Args:
        app: Flask application instance
    """
    if not app.debug:
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT,
            delay=True
        )
        file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))


def register_blueprints(app):
    """
    Register all route blueprints.

    Args:
        app: Flask application instance
    """
    from routes import register_routes
    register_routes(app)


# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
