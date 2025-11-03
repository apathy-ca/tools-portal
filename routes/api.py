"""
API routes with OpenAPI/Swagger documentation
"""

from flask import jsonify, current_app
from flask_restx import Api, Resource, fields
from datetime import datetime
from functools import wraps

from . import api_bp
from services.tools import tool_service

# Initialize Flask-RESTX API with Swagger documentation
api = Api(
    api_bp,
    version='2.1.0',
    title='Tools Portal API',
    description='API for managing and accessing network and system administration tools',
    doc='/docs',  # Swagger UI will be at /api/docs
    contact_email='admin@tools-portal.local',
    license='MIT'
)


def cache_response(timeout=300):
    """
    Decorator to cache API responses.

    Args:
        timeout: Cache timeout in seconds (default 5 minutes)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get cache from current app
            cache = current_app.cache
            cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            # Generate response and cache it
            response = f(*args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)
            return response

        return decorated_function
    return decorator

# Define API namespaces for organization
ns_tools = api.namespace('tools', description='Tool management operations')

# Define API models for request/response documentation
tool_feature = api.model('ToolFeature', {
    'feature': fields.String(description='Feature description')
})

tool_info = api.model('ToolInfo', {
    'name': fields.String(required=True, description='Tool name'),
    'description': fields.String(required=True, description='Tool description'),
    'version': fields.String(required=True, description='Tool version'),
    'url': fields.String(required=True, description='Tool URL path'),
    'icon': fields.String(description='Tool icon emoji'),
    'category': fields.String(description='Tool category'),
    'status': fields.String(description='Tool status (stable, beta, etc.)'),
    'features': fields.List(fields.String, description='List of tool features'),
    'tags': fields.List(fields.String, description='Tool tags')
})

category_info = api.model('CategoryInfo', {
    'icon': fields.String(description='Category icon emoji'),
    'description': fields.String(description='Category description')
})

tools_response = api.model('ToolsResponse', {
    'tools': fields.Raw(description='Dictionary of available tools'),
    'categories': fields.Raw(description='Dictionary of tool categories'),
    'total_tools': fields.Integer(description='Total number of tools'),
    'timestamp': fields.String(description='Response timestamp (ISO 8601)')
})


@ns_tools.route('')
class ToolsList(Resource):
    """Tool listing endpoint"""

    @ns_tools.doc('list_tools')
    @ns_tools.marshal_with(tools_response)
    @ns_tools.response(200, 'Success')
    @cache_response(timeout=300)  # Cache for 5 minutes
    def get(self):
        """
        Get list of all available tools.

        Returns a complete list of detected tools with their metadata,
        organized by categories.

        This endpoint is cached for 5 minutes to improve performance.
        """
        return {
            'tools': tool_service.tools,
            'categories': tool_service.categories,
            'total_tools': tool_service.get_tool_count(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


@ns_tools.route('/<string:tool_name>')
@ns_tools.param('tool_name', 'The tool identifier (e.g., dns-by-eye, ipwhale)')
class Tool(Resource):
    """Single tool information endpoint"""

    @ns_tools.doc('get_tool')
    @ns_tools.marshal_with(tool_info)
    @ns_tools.response(200, 'Success')
    @ns_tools.response(404, 'Tool not found')
    def get(self, tool_name):
        """
        Get information about a specific tool.

        Returns detailed information about a single tool including
        its features, version, and configuration.
        """
        tool_info = tool_service.get_tool_info(tool_name)
        if tool_info:
            return tool_info
        else:
            api.abort(404, f"Tool '{tool_name}' not found")
