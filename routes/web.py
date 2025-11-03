"""
Web routes for HTML pages and static content
"""

from flask import render_template, send_from_directory, current_app

from . import web_bp
from services.tools import tool_service


@web_bp.route('/')
def index():
    """
    Main tools portal landing page.

    Displays all detected tools organized by category.
    """
    return render_template('index.html',
                         tools=tool_service.tools,
                         categories=tool_service.categories)


@web_bp.route('/static/<path:filename>')
def static_files(filename):
    """
    Serve static files.

    Args:
        filename: Path to the static file

    Returns:
        Static file content
    """
    return send_from_directory(current_app.static_folder, filename)


@web_bp.app_errorhandler(404)
def not_found(error):
    """
    Custom 404 error page.

    Args:
        error: The error object

    Returns:
        404 error page
    """
    return render_template('404.html'), 404


@web_bp.app_errorhandler(500)
def internal_error(error):
    """
    Custom 500 error page.

    Args:
        error: The error object

    Returns:
        500 error page
    """
    return render_template('500.html'), 500
