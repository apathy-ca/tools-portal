# -*- coding: utf-8 -*-
"""
Tools Portal - Main Application
A collection of useful network and system administration tools with optional AI integration.
"""

from flask import Flask, render_template, send_from_directory, jsonify, request, redirect
import os
import json
import sys
import logging
import requests
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import Config

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.from_object(Config)

# AI Integration - Auto-detect Symposium backend
SYMPOSIUM_BACKEND_URL = os.environ.get('SYMPOSIUM_BACKEND_URL', 'http://localhost:8000')
SYMPOSIUM_AUTH_TOKEN = os.environ.get('SYMPOSIUM_AUTH_TOKEN', 'dev-token')
AI_FEATURES_AVAILABLE = False

def check_ai_backend():
    """Check if Symposium AI backend is available."""
    global AI_FEATURES_AVAILABLE
    try:
        response = requests.get(f"{SYMPOSIUM_BACKEND_URL}/health", timeout=5)
        AI_FEATURES_AVAILABLE = response.status_code == 200
        if AI_FEATURES_AVAILABLE:
            app.logger.info("✅ AI features enabled - Symposium backend detected")
        else:
            app.logger.info("ℹ️ AI features disabled - Symposium backend not responding")
    except Exception as e:
        AI_FEATURES_AVAILABLE = False
        app.logger.info(f"ℹ️ AI features disabled - Symposium backend not available: {str(e)}")
    return AI_FEATURES_AVAILABLE

def make_symposium_request(endpoint, method='GET', data=None, files=None):
    """Make a request to the Symposium backend with proper error handling."""
    if not AI_FEATURES_AVAILABLE:
        return {
            'success': False,
            'status_code': 503,
            'data': {'error': 'AI features not available - Symposium backend not connected'}
        }
    
    try:
        url = f"{SYMPOSIUM_BACKEND_URL}{endpoint}"
        headers = {
            'Authorization': f'Bearer {SYMPOSIUM_AUTH_TOKEN}'
        }
        
        if files:
            response = requests.request(method, url, headers=headers, data=data, files=files, timeout=30)
        else:
            if data:
                headers['Content-Type'] = 'application/json'
                data = json.dumps(data) if isinstance(data, dict) else data
            response = requests.request(method, url, headers=headers, data=data, timeout=30)
        
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {'error': 'Invalid JSON response from Symposium backend'}
        
        return {
            'success': response.status_code < 400,
            'status_code': response.status_code,
            'data': response_data
        }
        
    except requests.RequestException as e:
        app.logger.error(f"Symposium API request failed: {str(e)}")
        return {
            'success': False,
            'status_code': 0,
            'data': {'error': f'Connection error: {str(e)}'}
        }

# Initialize AI backend check
check_ai_backend()

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
        'version': '1.3.0',
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
    },
    'ipwhale': {
        'name': 'IP Whale',
        'description': 'IP address information tool with IPv4/IPv6 detection, PTR records, ASN lookup, and NAT detection',
        'version': '1.0.0',
        'url': '/ipwhale/',
        'icon': '🐋',
        'category': 'DNS & Networking',
        'status': 'stable',
        'features': [
            'IPv4 and IPv6 detection',
            'PTR record lookup',
            'ASN information',
            'NAT detection',
            'Remote port detection',
            'Curl-friendly API endpoints'
        ],
        'tags': ['ip', 'networking', 'asn', 'ptr', 'nat-detection']
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
    """Main tools portal landing page with conditional AI integration."""
    return render_template('index.html',
                         tools=TOOLS,
                         categories=CATEGORIES,
                         ai_features_available=AI_FEATURES_AVAILABLE)

@app.route('/api/tools')
def api_tools():
    """API endpoint to get list of available tools."""
    return jsonify({
        'tools': TOOLS,
        'categories': CATEGORIES,
        'total_tools': len(TOOLS),
        'ai_integration': AI_FEATURES_AVAILABLE,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'tools-portal',
        'ai_integration': AI_FEATURES_AVAILABLE,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'tools_available': len(TOOLS)
    })

# AI Integration Endpoints (only active when backend available)
@app.route('/api/ai/health')
def ai_health_check():
    """Check Symposium backend health and refresh connection status."""
    check_ai_backend()  # Refresh status
    
    if AI_FEATURES_AVAILABLE:
        result = make_symposium_request('/health')
        if result['success']:
            return jsonify({
                'status': 'connected',
                'symposium_backend': result['data'],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
    
    return jsonify({
        'status': 'disconnected',
        'error': 'Symposium backend not available',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 503

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Send message to AI Sage."""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI features not available - Symposium backend not connected'}), 503
    
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Message content is required'}), 400
        
        chat_request = {
            'content': data['content'],
            'sage_id': data.get('sage_id'),
            'model_preference': data.get('model_preference')
        }
        
        sage_id = data.get('sage_id')
        if sage_id and sage_id.startswith('sage_'):
            result = make_symposium_request(f'/sages/{sage_id}/message', 'POST', chat_request)
        else:
            result = make_symposium_request('/conversations', 'POST', chat_request)
        
        if result['success']:
            return jsonify(result['data'])
        else:
            return jsonify(result['data']), result['status_code'] or 500
            
    except Exception as e:
        app.logger.error(f"AI chat error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai/sages')
def ai_get_sages():
    """Get available AI Sages."""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({
            'sages': [{
                'id': 'demo-sage',
                'name': 'Demo AI',
                'personality_type': 'assistant',
                'state': 'demo',
                'description': 'Demo mode - connect Symposium backend for full AI features.',
                'beliefs': {
                    'core_values': ['helpfulness', 'learning'],
                    'philosophical_stance': 'AI features available when Symposium backend is connected.',
                    'curiosities': ['networking', 'system administration']
                }
            }],
            'count': 1,
            'demo_mode': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    result = make_symposium_request('/sages/')
    if result['success']:
        return jsonify(result['data'])
    else:
        return jsonify(result['data']), result['status_code'] or 500

@app.route('/api/ai/models')
def ai_get_models():
    """Get available AI models."""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({
            'models': ['demo-mode'],
            'categorized': {'demo': ['demo-mode']},
            'total_count': 1,
            'demo_mode': True
        })
    
    sage_id = request.args.get('sage_id')
    if sage_id and sage_id.startswith('sage_'):
        result = make_symposium_request(f'/sages/{sage_id}/models')
    else:
        result = make_symposium_request('/llm/models')
    
    if result['success']:
        return jsonify(result['data'])
    else:
        return jsonify(result['data']), result['status_code'] or 500

@app.route('/api/ai/upload', methods=['POST'])
def ai_upload_file():
    """Upload file for AI analysis."""
    if not AI_FEATURES_AVAILABLE:
        return jsonify({'error': 'AI file analysis not available - Symposium backend not connected'}), 503
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        files = {'file': (file.filename, file.stream, file.mimetype)}
        result = make_symposium_request('/files/upload', 'POST', files=files)
        
        if result['success']:
            return jsonify(result['data'])
        else:
            return jsonify(result['data']), result['status_code'] or 500
            
    except Exception as e:
        app.logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

@app.route('/api/health/detailed')
def detailed_health():
    """Detailed health check endpoint including AI integration."""
    import psutil
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': getattr(Config, 'VERSION', '1.0.0'),
        'service': 'tools-portal',
        'ai_integration': AI_FEATURES_AVAILABLE,
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
    
    # Check IP Whale service
    try:
        response = requests.get('http://ipwhale:5000/api/health', timeout=5)
        health_status['dependencies']['ipwhale'] = {
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'response_time': response.elapsed.total_seconds()
        }
    except Exception as e:
        health_status['dependencies']['ipwhale'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Check Symposium AI backend
    check_ai_backend()  # Refresh status
    if AI_FEATURES_AVAILABLE:
        ai_health = make_symposium_request('/health')
        health_status['dependencies']['symposium-ai'] = {
            'status': 'healthy' if ai_health['success'] else 'unhealthy',
            'error': ai_health['data'].get('error') if not ai_health['success'] else None
        }
    else:
        health_status['dependencies']['symposium-ai'] = {
            'status': 'not_configured',
            'note': 'AI features disabled - Symposium backend not available'
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
    
    # Determine overall status (AI backend issues don't affect overall health)
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
