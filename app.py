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
from dynamic_tools import detect_available_tools, get_tool_categories, check_tool_health

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
    app.logger.info('Tools Portal startup - Dynamic tool detection enabled')

# Dynamic tool detection - automatically discovers tools from submodules
print("🔍 Detecting available tools...")
TOOLS = detect_available_tools()
CATEGORIES = get_tool_categories(TOOLS)

print(f"✅ Detected {len(TOOLS)} tools: {', '.join(TOOLS.keys())}")

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
    """Detailed health check endpoint with dynamic tool detection."""
    import psutil
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': Config.VERSION,
        'service': 'tools-portal',
        'dependencies': {},
        'metrics': {},
        'detected_tools': list(TOOLS.keys())
    }
    
    # Dynamically check all detected tools
    for tool_name in TOOLS.keys():
        health_status['dependencies'][tool_name] = check_tool_health(tool_name)
    
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

@app.route('/ipwhale/')
def ipwhale_redirect():
    """Redirect to IP Whale tool - this will be handled by nginx proxy."""
    return redirect('/')

@app.route('/ipwhale/<path:path>')
def ipwhale_subpaths(path):
    """Handle IP Whale subpaths - this will be handled by nginx proxy."""
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
