import pytest
import json
import sys
import os

# Add the tools-portal directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools-portal'))

from app import app, TOOLS, CATEGORIES

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Test the main index page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Tools Portal' in response.data

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'tools-portal'
    assert 'timestamp' in data

def test_detailed_health_check(client):
    """Test the detailed health check endpoint."""
    response = client.get('/api/health/detailed')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
    assert 'version' in data
    assert 'dependencies' in data
    assert 'metrics' in data

def test_api_tools(client):
    """Test the tools API endpoint."""
    response = client.get('/api/tools')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'tools' in data
    assert 'categories' in data
    assert data['total_tools'] == len(TOOLS)

def test_static_files(client):
    """Test static file serving."""
    response = client.get('/static/favicon.png')
    # Should either return the file or 404 if it doesn't exist
    assert response.status_code in [200, 404]

def test_404_error(client):
    """Test 404 error handling."""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404

def test_tools_registry():
    """Test that the tools registry is properly structured."""
    assert isinstance(TOOLS, dict)
    assert len(TOOLS) > 0
    
    for tool_id, tool_info in TOOLS.items():
        assert 'name' in tool_info
        assert 'description' in tool_info
        assert 'version' in tool_info
        assert 'url' in tool_info
        assert 'category' in tool_info
        assert 'status' in tool_info

def test_categories_registry():
    """Test that the categories registry is properly structured."""
    assert isinstance(CATEGORIES, dict)
    assert len(CATEGORIES) > 0
    
    for category_id, category_info in CATEGORIES.items():
        assert 'icon' in category_info
        assert 'description' in category_info
