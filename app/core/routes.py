"""
Tools Portal v2 - Core Routes
Main dashboard, API endpoints, and health checks.
"""
from flask import Blueprint, render_template, jsonify, current_app
from datetime import datetime
import psutil

bp = Blueprint('core', __name__)


@bp.route('/')
def index():
    """Main dashboard showing all available tools."""
    tools = current_app.config.get('TOOLS', {})
    categories = current_app.config.get('CATEGORIES', {})

    return render_template(
        'index.html',
        tools=tools,
        categories=categories,
        version=current_app.config.get('VERSION', '2.0.0')
    )


@bp.route('/api/tools')
def api_tools():
    """API endpoint listing all available tools."""
    tools = current_app.config.get('TOOLS', {})
    categories = current_app.config.get('CATEGORIES', {})

    return jsonify({
        'tools': tools,
        'categories': categories,
        'total_tools': len(tools),
        'version': current_app.config.get('VERSION', '2.0.0'),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


@bp.route('/health')
@bp.route('/api/health')
def health():
    """Basic health check."""
    return jsonify({
        'status': 'healthy',
        'service': 'tools-portal',
        'version': current_app.config.get('VERSION', '2.0.0'),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


@bp.route('/api/health/detailed')
def health_detailed():
    """Detailed health check with system metrics."""
    tools = current_app.config.get('TOOLS', {})

    health_data = {
        'status': 'healthy',
        'service': 'tools-portal',
        'version': current_app.config.get('VERSION', '2.0.0'),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'tools': {
            'total': len(tools),
            'registered': list(tools.keys())
        },
        'metrics': {}
    }

    # System metrics
    try:
        health_data['metrics'] = {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    except Exception as e:
        health_data['metrics']['error'] = str(e)

    return jsonify(health_data)


@bp.errorhandler(404)
def not_found(error):
    """404 error handler."""
    if current_app.config.get('DEBUG'):
        return jsonify({'error': 'Not found', 'path': error.description}), 404
    return render_template('404.html'), 404


@bp.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    current_app.logger.error(f'Internal error: {error}')
    if current_app.config.get('DEBUG'):
        return jsonify({'error': 'Internal server error', 'details': str(error)}), 500
    return render_template('500.html'), 500
