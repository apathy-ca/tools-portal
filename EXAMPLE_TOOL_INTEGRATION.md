# Example Tool Integration Guide

This document demonstrates how to properly integrate a new tool into the Tools Portal using a generic example.

## Overview

The Tools Portal uses a dynamic tool detection system that automatically discovers and integrates tools placed in the `tools/` directory. This guide shows the complete integration process.

## Tool Structure

A properly integrated tool should have this structure:

```
tools/your-tool-name/
├── Dockerfile              # Required: Container configuration
├── config.py               # Optional: Tool metadata for portal
├── [application files]     # Your tool's source code
└── README.md               # Tool-specific documentation
```

## Example Tool Configuration

### 1. Tool Configuration (`config.py`)

```python
"""
Tool Configuration for Tools Portal Dynamic Detection
"""

TOOL_INFO = {
    'name': 'Your Tool Name',
    'description': 'Brief description of what your tool does',
    'version': '1.0.0',
    'url': '/your-tool-name/',
    'icon': '🔧',
    'category': 'Utilities',
    'status': 'stable',
    'features': [
        'Feature 1',
        'Feature 2',
        'Feature 3',
        'Responsive design for all devices'
    ],
    'tags': ['utility', 'tool', 'example']
}
```

### 2. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port 5000 (standard for tools-portal)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start the application
CMD ["python", "app.py"]
```

### 3. Health Check Endpoint

Every tool must provide a health check endpoint at `/api/health`:

```python
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'your-tool-name',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': '1.0.0'
    })
```

## Integration Process

### Step 1: Place Tool in Directory
```bash
# Copy your tool to the tools directory
cp -r your-tool tools-portal/tools/your-tool-name/
```

### Step 2: Generate Configuration
```bash
cd tools-portal
python generate-compose.py
```

This automatically:
- Detects the new tool (looks for Dockerfile)
- Loads tool configuration from `config.py` if present
- Generates docker-compose files with the new service
- Updates nginx configuration with routing
- Adds the tool to the portal's tool registry

### Step 3: Deploy
```bash
# Standard deployment
docker-compose -f docker-compose-tools.yaml up --build

# SSL deployment
docker-compose -f docker-compose-tools-ssl.yaml up --build
```

## Dynamic Detection Features

### Tool Discovery
The system automatically detects tools by:
1. Scanning the `tools/` directory
2. Looking for directories with a `Dockerfile`
3. Loading configuration from `config.py` if present
4. Generating default configuration if no `config.py` exists

### Configuration Loading
Priority order for tool configuration:
1. **Tool's `config.py`** - Custom configuration with `TOOL_INFO`
2. **Known tool defaults** - Predefined configurations in `generate-compose.py`
3. **Generated defaults** - Basic configuration based on directory name

### Category Support
Supported categories (automatically detected):
- DNS & Networking
- Security
- System Administration
- Development
- Gaming & Entertainment
- Utilities (default)

## Best Practices

### 1. Tool Configuration
- Always provide a `config.py` with `TOOL_INFO`
- Use descriptive names and clear descriptions
- Choose appropriate categories and icons
- List key features and tags for discoverability

### 2. Container Standards
- Use port 5000 for consistency
- Implement health check endpoint at `/api/health`
- Use lightweight base images
- Include proper health check in Dockerfile

### 3. Documentation
- Include a README.md in your tool directory
- Document API endpoints if applicable
- Provide usage examples
- List dependencies and requirements

### 4. Security
- Implement proper input validation
- Use non-root containers when possible
- Follow security best practices for your technology stack
- Implement rate limiting if needed

## Testing Integration

### 1. Verify Detection
```bash
cd tools-portal
python dynamic_tools.py
```

### 2. Check Generated Files
- `docker-compose-tools.yaml` - Should include your tool service
- `nginx-tools.conf` - Should include routing for your tool
- Tool should appear in portal's tool registry

### 3. Test Deployment
```bash
# Build and test
docker compose -f docker-compose-tools.yaml up --build your-tool-name

# Test health endpoint
curl http://localhost:5000/api/health
```

## Troubleshooting

### Tool Not Detected
- Ensure `Dockerfile` exists in tool directory
- Check that directory is directly under `tools/`
- Verify no syntax errors in `config.py`

### Build Failures
- Check Dockerfile syntax
- Verify all dependencies are listed in requirements
- Ensure base image is available

### Routing Issues
- Regenerate configuration: `python generate-compose.py`
- Check nginx configuration includes your tool
- Verify tool responds on port 5000

## Example Tools

Current integrated tools demonstrate:
- ✅ DNS analysis and visualization (dns-by-eye)
- ✅ IP geolocation and analysis (ipwhale)
- ✅ Proper health check implementation
- ✅ Complete tool configuration
- ✅ Category assignment
- ✅ Feature-rich descriptions
- ✅ Responsive design

These serve as reference implementations for integrating tools with the portal.

## Support

For questions about tool integration:
1. Review this example implementation
2. Check the dynamic detection logs
3. Verify your tool follows the required structure
4. Test individual components before full integration

---

**Tools Portal Dynamic Integration** - Automatic tool detection and deployment