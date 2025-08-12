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
def dns_by_eye_redirect():
    """Redirect to DNS By Eye tool with helpful message."""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DNS By Eye - Tools Portal</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
                color: white;
                text-align: center;
            }
            .container {
                max-width: 600px;
                padding: 2rem;
            }
            .title {
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
            .message {
                font-size: 1.2rem;
                margin-bottom: 2rem;
                opacity: 0.9;
            }
            .button {
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 1rem 2rem;
                border-radius: 10px;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                margin: 0.5rem;
            }
            .button:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }
            .info {
                margin-top: 2rem;
                padding: 1rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="title">🔍 DNS By Eye</div>
            <div class="message">
                DNS delegation visualizer with health scoring and glue record analysis
            </div>
            <a href="/" class="button">🏠 Back to Tools Portal</a>
            <div class="info">
                <h3>🚧 Tool Integration in Progress</h3>
                <p>DNS By Eye is being integrated into the new Tools Portal architecture. 
                The tool will be available shortly at this location.</p>
                <p><strong>Features:</strong></p>
                <ul style="text-align: left; display: inline-block;">
                    <li>DNS delegation tracing</li>
                    <li>Visual graph generation</li>
                    <li>Health score calculation</li>
                    <li>Smart graph condensation (4+ nameservers)</li>
                    <li>Enhanced glue record analysis</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/dns-by-eye/<path:path>')
def dns_by_eye_subpaths(path):
    """Handle DNS By Eye subpaths."""
    return redirect('/dns-by-eye/')

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
