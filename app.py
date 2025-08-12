# -*- coding: utf-8 -*-
"""
Tools Portal - Main Application
A collection of useful network and system administration tools.
"""

from flask import Flask, render_template, send_from_directory, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__, static_folder="static", static_url_path="/static")

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
    app.run(host='0.0.0.0', port=5000, debug=True)
