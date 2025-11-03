# Tools Portal - Architecture Documentation

## Overview

Tools Portal uses a modular architecture with clear separation of concerns, making it easy to maintain, test, and extend.

## Architecture Pattern

The application follows a **Blueprint-based modular design** with:
- **Application Factory Pattern** for flexible app initialization
- **Service Layer** for business logic
- **Route Blueprints** for organized endpoint management
- **OpenAPI/Swagger** for automatic API documentation

## Directory Structure

```
tools-portal/
├── app.py                    # Application factory and initialization
├── config.py                 # Configuration management
├── gunicorn_config.py        # WSGI server configuration
├── dynamic_tools.py          # Low-level tool detection
├──
├── routes/                   # Route blueprints
│   ├── __init__.py          # Blueprint registration
│   ├── api.py               # API endpoints with Swagger docs
│   ├── health.py            # Health check endpoints
│   └── web.py               # Web pages and static files
├──
├── services/                 # Business logic layer
│   ├── __init__.py
│   └── tools.py             # Tool discovery service
├──
├── templates/               # Jinja2 templates
│   ├── index.html
│   ├── 404.html
│   └── 500.html
├──
├── static/                  # Static assets
│   └── favicon.png
├──
└── tests/                   # Unit tests
    ├── __init__.py
    ├── test_app.py
    └── README.md
```

## Components

### 1. Application Core (`app.py`)

**Purpose**: Application initialization and configuration

**Key Functions**:
- `create_app()` - Application factory
- `initialize_extensions()` - Set up Flask extensions (caching, etc.)
- `configure_logging()` - Configure application logging
- `register_blueprints()` - Register all route blueprints

**Benefits**:
- Testable (can create app instances with different configs)
- Clean separation of concerns
- Easy to extend with new extensions

### 2. Routes Layer (`routes/`)

**Purpose**: Handle HTTP requests and responses

#### `routes/api.py` - API Endpoints
- **Framework**: Flask-RESTX for OpenAPI/Swagger
- **Documentation**: Automatic Swagger UI at `/api/docs`
- **Endpoints**:
  - `GET /api/tools` - List all tools (cached 5 min)
  - `GET /api/tools/<tool_name>` - Get specific tool info
- **Features**:
  - Request/response validation
  - Automatic API documentation
  - Response caching

#### `routes/health.py` - Health Checks
- **Endpoints**:
  - `GET /health` - Basic health check
  - `GET /api/health/detailed` - Detailed health with dependencies
- **Features**:
  - Dynamic tool health checking
  - System metrics (CPU, memory, disk)
  - Enhanced error logging

#### `routes/web.py` - Web Interface
- **Endpoints**:
  - `GET /` - Landing page
  - `GET /static/<path>` - Static files
  - Error handlers (404, 500)
- **Features**:
  - Server-side rendering
  - Custom error pages

### 3. Services Layer (`services/`)

**Purpose**: Business logic and data access

#### `services/tools.py` - Tool Service
- **Responsibility**: Centralized tool management
- **Key Methods**:
  - `tools` - Property to get all tools
  - `categories` - Property to get categories
  - `get_tool_count()` - Number of detected tools
  - `get_tool_info(tool_name)` - Get specific tool
  - `tool_exists(tool_name)` - Check if tool exists
- **Benefits**:
  - Single source of truth for tool data
  - Easy to mock for testing
  - Encapsulates tool discovery logic

### 4. Tool Discovery (`dynamic_tools.py`)

**Purpose**: Low-level tool detection from filesystem

**Key Functions**:
- `detect_available_tools()` - Scan tools/ directory
- `get_tool_categories()` - Organize tools by category
- `load_tool_config()` - Load tool metadata

## Data Flow

```
HTTP Request
    ↓
Routes (Blueprint)
    ↓
Services (Business Logic)
    ↓
Dynamic Tools (Data Access)
    ↓
Response (JSON/HTML)
```

## API Documentation

### Swagger UI

Access interactive API docs at: **`http://your-domain.com/api/docs`**

Features:
- Try endpoints directly from browser
- View request/response schemas
- Download OpenAPI spec (JSON/YAML)

### API Models

```python
ToolInfo:
  - name: str
  - description: str
  - version: str
  - url: str
  - icon: str
  - category: str
  - status: str
  - features: [str]
  - tags: [str]

ToolsResponse:
  - tools: dict
  - categories: dict
  - total_tools: int
  - timestamp: str
```

## Caching Strategy

| Endpoint | Cache Duration | Reason |
|----------|---------------|---------|
| `/api/tools` | 5 minutes | Tool list rarely changes |
| `/api/health/detailed` | 1 minute | Balance freshness vs performance |
| `/health` | No cache | Fast enough without caching |

## Error Handling

### Logging Levels

- **Exception**: Full stack trace (health checks, system metrics)
- **Error**: Error without stack trace
- **Warning**: Unusual but handled situations
- **Info**: Normal operations (startup, shutdown)

### Error Responses

```json
{
  "error": "Detailed error message",
  "error_type": "ExceptionClassName"
}
```

## Testing

### Test Organization

```
tests/
├── test_app.py          # Main test suite
│   ├── ToolsPortalTestCase
│   │   ├── test_health_endpoint
│   │   ├── test_tools_api_endpoint
│   │   ├── test_tools_api_caching
│   │   ├── test_index_page
│   │   ├── test_404_handler
│   │   ├── test_static_files
│   │   └── test_detailed_health_*
│   └── DynamicToolDiscoveryTestCase
│       ├── test_tools_detected
│       └── test_tool_structure
```

### Running Tests

```bash
# Using unittest
python -m unittest discover tests -v

# Using pytest (with coverage)
pytest --cov=app --cov=routes --cov=services --cov-report=html
```

## Adding New Features

### 1. Adding a New API Endpoint

**File**: `routes/api.py`

```python
@ns_tools.route('/new-endpoint')
class NewEndpoint(Resource):
    @ns_tools.doc('description')
    @cache_response(timeout=300)  # Optional caching
    def get(self):
        """Endpoint description"""
        return {'data': 'value'}
```

### 2. Adding a New Service

**File**: `services/new_service.py`

```python
class NewService:
    def __init__(self):
        # Initialize service
        pass

    def do_something(self):
        # Business logic
        return result

# Global instance
new_service = NewService()
```

**Usage in routes**:
```python
from services.new_service import new_service
```

### 3. Adding a New Web Page

**File**: `routes/web.py`

```python
@web_bp.route('/new-page')
def new_page():
    return render_template('new_page.html', data=data)
```

## Security Considerations

1. **Non-root user**: Docker container runs as `appuser`
2. **Input validation**: Flask-RESTX validates all API inputs
3. **Error handling**: Never expose internal errors to users
4. **Logging**: Sensitive data not logged
5. **Caching**: Cache keys don't include sensitive data

## Performance Optimizations

1. **Response Caching**: Reduces backend load by 90%+
2. **Blueprint Registration**: Lazy loading of routes
3. **Service Singletons**: Tool discovery runs once on startup
4. **Connection Pooling**: Reuse HTTP connections for health checks

## Monitoring

### Health Check Endpoints

- **Basic**: `GET /health`
  - Returns: Service status, timestamp, tool count
  - Use: Load balancer health checks

- **Detailed**: `GET /api/health/detailed`
  - Returns: Dependencies, system metrics, version
  - Use: Monitoring dashboards, debugging

### Metrics Available

- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- Tool health status
- Response times

## Extension Points

The architecture is designed to be easily extensible:

1. **New Routes**: Add new blueprint in `routes/`
2. **New Services**: Add new service in `services/`
3. **New Tools**: Just add to `tools/` directory
4. **New Middleware**: Add in `app.py` initialization
5. **New Extensions**: Initialize in `initialize_extensions()`

## Deployment

### Docker Build

The Dockerfile copies all necessary components:

```dockerfile
COPY --chown=appuser:appuser app.py config.py gunicorn_config.py dynamic_tools.py ./
COPY --chown=appuser:appuser routes/ routes/
COPY --chown=appuser:appuser services/ services/
COPY --chown=appuser:appuser templates/ templates/
COPY --chown=appuser:appuser static/ static/
```

### Environment Variables

See `config.py` for all available configuration options.

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
1. Ensure `routes/` and `services/` have `__init__.py`
2. Check `PYTHONPATH` includes project root
3. Verify Dockerfile copies all directories

### Cache Not Working

1. Check `app.cache` is initialized
2. Verify `@cache_response` decorator is applied
3. Clear cache: `app.cache.clear()`

### API Documentation Not Showing

1. Visit `/api/docs` (not `/api/documentation`)
2. Ensure Flask-RESTX is installed
3. Check for blueprint registration errors in logs

## Future Enhancements

Potential improvements to consider:

1. **Database Integration**: SQLAlchemy for persistent data
2. **Redis Caching**: Replace simple cache with Redis
3. **Rate Limiting**: Add per-endpoint rate limits
4. **Authentication**: JWT or OAuth2 for API access
5. **Webhooks**: Tool status change notifications
6. **GraphQL API**: Alternative to REST API

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-RESTX Documentation](https://flask-restx.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Application Factory Pattern](https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/)
