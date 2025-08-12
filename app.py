# -*- coding: utf-8 -*-
"""
Tools Portal - Main Application
A collection of useful network and system administration tools.
"""

from flask import Flask, render_template, send_from_directory, jsonify, request, redirect
import os
import json
import sys
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

@app.route('/dns-by-eye/')
@app.route('/dns-by-eye/<path:path>')
def dns_by_eye_tool(path=''):
    """Route DNS By Eye tool requests."""
    try:
        # Add the DNS By Eye app directory to Python path
        dns_by_eye_path = os.path.join(os.path.dirname(__file__), 'tools', 'dns-by-eye')
        if dns_by_eye_path not in sys.path:
            sys.path.insert(0, dns_by_eye_path)
        
        # Import the DNS By Eye app
        from app.main import app as dns_app
        
        # Create a test client and make the request
        with dns_app.test_client() as client:
            # Forward the request to DNS By Eye
            if request.method == 'GET':
                response = client.get(f'/{path}', query_string=request.query_string)
            elif request.method == 'POST':
                response = client.post(f'/{path}', 
                                     data=request.get_data(),
                                     content_type=request.content_type,
                                     query_string=request.query_string)
            else:
                response = client.open(f'/{path}', 
                                     method=request.method,
                                     data=request.get_data(),
                                     content_type=request.content_type,
                                     query_string=request.query_string)
            
            # Return the response from DNS By Eye
            return response.get_data(as_text=True), response.status_code, dict(response.headers)
                
    except ImportError as e:
        # DNS By Eye not available, show error message
        return f"DNS By Eye tool is not available. Error: {str(e)}", 503
    except Exception as e:
        # Other errors
        return f"Error loading DNS By Eye: {str(e)}", 500

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
