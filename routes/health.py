"""
Health check routes
"""

from flask import jsonify, current_app
from datetime import datetime
import requests
import psutil

from . import health_bp
from services.tools import tool_service
from config import Config


@health_bp.route('/health')
def health_check():
    """
    Basic health check endpoint.

    Returns:
        JSON response with basic health status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'tools-portal',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'tools_available': tool_service.get_tool_count()
    })


@health_bp.route('/api/health/detailed')
def detailed_health():
    """
    Detailed health check endpoint with dynamic tool discovery.
    Includes system metrics and dependency health checks.

    Returns:
        JSON response with detailed health information
    """
    # Note: This could use caching but we'll add that in the API routes
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': getattr(Config, 'VERSION', '1.0.0'),
        'service': 'tools-portal',
        'dependencies': {},
        'metrics': {}
    }

    # Dynamically check all detected tools
    for tool_name in tool_service.tools.keys():
        try:
            response = requests.get(f'http://{tool_name}:5000/api/health', timeout=5)
            health_status['dependencies'][tool_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            current_app.logger.exception(f"Health check failed for {tool_name}")
            health_status['dependencies'][tool_name] = {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': type(e).__name__
            }

    # System metrics
    try:
        health_status['metrics'] = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    except Exception as e:
        current_app.logger.exception("Failed to collect system metrics")
        health_status['metrics']['error'] = {
            'message': str(e),
            'type': type(e).__name__
        }

    # Determine overall status
    unhealthy_deps = [dep for dep in health_status['dependencies'].values()
                     if dep.get('status') == 'unhealthy']
    if unhealthy_deps:
        health_status['status'] = 'degraded'

    return jsonify(health_status)
