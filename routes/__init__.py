"""
Routes module for Tools Portal
"""

from flask import Blueprint

# Create blueprints
api_bp = Blueprint('api', __name__, url_prefix='/api')
health_bp = Blueprint('health', __name__)
web_bp = Blueprint('web', __name__)


def register_routes(app):
    """Register all route blueprints with the Flask app."""
    from . import api, health, web

    app.register_blueprint(api_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(web_bp)
