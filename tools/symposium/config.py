"""
Symposium Tool Configuration
AI consciousness exploration platform configuration for tools-portal integration.
"""

# Tool information for dynamic detection
TOOL_INFO = {
    'name': 'Symposium',
    'description': 'AI consciousness exploration platform with multiple AI Sages for intelligent conversations',
    'version': '1.0.0',
    'url': '/symposium/',
    'icon': '🧠',
    'category': 'AI & Consciousness',
    'status': 'stable',
    'features': [
        'Multiple AI Sage personalities',
        'Intelligent conversation management',
        'File upload and analysis',
        'Model selection and preferences',
        'Persistent conversation history',
        'Consciousness exploration'
    ],
    'tags': ['ai', 'consciousness', 'chat', 'sage', 'llm']
}

# Application configuration
class Config:
    # Next.js specific settings
    NODE_ENV = 'production'
    NEXT_PUBLIC_API_URL = '/api'
    
    # Integration with symposium backend
    SYMPOSIUM_BACKEND_URL = 'http://symposium-backend:8000'
    
    # Container settings
    PORT = 3000
    HOST = '0.0.0.0'