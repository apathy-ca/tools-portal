# -*- coding: utf-8 -*-
"""
Tools Portal - Main Application
A collection of useful network and system administration tools.
"""

from flask import Flask, render_template, send_from_directory, jsonify, request, redirect
import os
import logging
import requests
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask_caching import Cache
from config import Config
from dynamic_tools import detect_available_tools, get_tool_categories

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.from_object(Config)

# Initialize caching
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',  # In-memory cache
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default
})

# Configure logging
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
    app.logger.info('Tools Portal startup')

# Dynamically detect available tools
app.logger.info('Detecting available tools...')
TOOLS = detect_available_tools()
CATEGORIES = get_tool_categories(TOOLS)
app.logger.info(f'Detected {len(TOOLS)} tools in {len(CATEGORIES)} categories')

@app.route('/')
def index():
    """Main tools portal landing page."""
    return render_template('index.html',
                         tools=TOOLS,
                         categories=CATEGORIES)

@app.route('/api/tools')
@cache.cached(timeout=300)  # Cache for 5 minutes
def api_tools():
    """API endpoint to get list of available tools."""
    return jsonify({
        'tools': TOOLS,
        'categories': CATEGORIES,
        'total_tools': len(TOOLS),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'tools-portal',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'tools_available': len(TOOLS)
    })

@app.route('/api/health/detailed')
@cache.cached(timeout=60)  # Cache for 1 minute
def detailed_health():
    """Detailed health check endpoint with dynamic tool discovery."""
    import psutil

    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': getattr(Config, 'VERSION', '1.0.0'),
        'service': 'tools-portal',
        'dependencies': {},
        'metrics': {}
    }

    # Dynamically check all detected tools
    for tool_name in TOOLS.keys():
        try:
            response = requests.get(f'http://{tool_name}:5000/api/health', timeout=5)
            health_status['dependencies'][tool_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            app.logger.exception(f"Health check failed for {tool_name}")
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
        app.logger.exception("Failed to collect system metrics")
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

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)

@app.errorhandler(404)
def not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 page."""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
