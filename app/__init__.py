"""
Tools Portal v2 - Application Factory
Clean, simplified Flask application with plugin architecture.
"""
from flask import Flask
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler

from app.config import Config
from app.tools import discover_tools, get_tool_categories

# Initialize extensions
cache = Cache()


def create_app(config_class=Config):
    """
    Application factory.

    Args:
        config_class: Configuration class to use

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    cache.init_app(app, config={
        'CACHE_TYPE': app.config['CACHE_TYPE'],
        'CACHE_DEFAULT_TIMEOUT': app.config['CACHE_DEFAULT_TIMEOUT'],
        'CACHE_REDIS_URL': app.config.get('REDIS_URL')
    })

    # Configure logging
    configure_logging(app)

    # Discover and register tool plugins
    app.logger.info("=" * 50)
    app.logger.info("Tools Portal v2 Starting")
    app.logger.info("=" * 50)

    tools = discover_tools(app)
    categories = get_tool_categories(tools)

    # Store in app context for templates
    app.config['TOOLS'] = tools
    app.config['CATEGORIES'] = categories

    # Register core routes
    from app.core import routes as core_routes
    app.register_blueprint(core_routes.bp)

    app.logger.info(f"Loaded {len(tools)} tools in {len(categories)} categories")
    app.logger.info("=" * 50)

    return app


def configure_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        # File handler
        file_handler = RotatingFileHandler(
            'tools_portal.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)

    app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
