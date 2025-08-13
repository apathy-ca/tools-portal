# -*- coding: utf-8 -*-
"""
Tools Portal - Main Application
A collection of useful network and system administration tools.
"""

from flask import Flask, render_template, send_from_directory, jsonify, request, redirect
import os
import json
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import Config

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.from_object(Config)

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

# Tool registry - add new tools here
TOOLS = {
    'dns-by-eye': {
        'name': 'DNS By Eye',
        'description': 'DNS delegation visualizer with health scoring and glue record analysis',
        'version': '1.0.2',
        'url': '/dns-by-eye/',
        'icon': '🔍',
        'category': 'DNS & Networking',
        'status': 'stable',
        'features': [
            'DNS delegation tracing',
            'Visual graph generation',
            'Health score calculation',
            'Glue record validation',
            'Multi-domain comparison',
            'Export capabilities'
        ],
        'tags': ['dns', 'networking', 'visualization', 'debugging']
    }
    # Future tools will be added here
}

CATEGORIES = {
    'DNS & Networking': {
        'icon': '🌐',
        'description': 'Tools for DNS analysis, network diagnostics, and connectivity testing'
    },
    'Security': {
        'icon': '🔒',
        'description': 'Security analysis, vulnerability scanning, and penetration testing tools'
    },
    'System Administration': {
        'icon': '⚙️',
        'description': 'Server management, monitoring, and system diagnostic utilities'
    },
    'Development': {
        'icon': '💻',
        'description': 'Developer tools, code analysis, and debugging utilities'
    }
}

@app.route('/')
def index():
    """Main tools portal landing page."""
    return render_template('index.html', tools=TOOLS, categories=CATEGORIES)

@app.route('/api/tools')
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
def detailed_health():
    """Detailed health check endpoint."""
    import psutil
    import requests
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': Config.VERSION,
        'service': 'tools-portal',
        'dependencies': {},
        'metrics': {}
    }
    
    # Check DNS By Eye service
    try:
        response = requests.get('http://dns-by-eye:5000/api/health', timeout=5)
        health_status['dependencies']['dns-by-eye'] = {
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'response_time': response.elapsed.total_seconds()
        }
    except Exception as e:
        health_status['dependencies']['dns-by-eye'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # System metrics
    try:
        health_status['metrics'] = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    except Exception as e:
        health_status['metrics']['error'] = str(e)
    
    # Determine overall status
    unhealthy_deps = [dep for dep in health_status['dependencies'].values() 
                     if dep.get('status') == 'unhealthy']
    if unhealthy_deps:
        health_status['status'] = 'degraded'
    
    return jsonify(health_status)

@app.route('/dns-by-eye/')
def dns_by_eye_redirect():
    """Redirect to DNS By Eye tool - this will be handled by nginx proxy."""
    return redirect('/')

@app.route('/dns-by-eye/<path:path>')
def dns_by_eye_subpaths(path):
    """Handle DNS By Eye subpaths - this will be handled by nginx proxy."""
    return redirect('/')

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
