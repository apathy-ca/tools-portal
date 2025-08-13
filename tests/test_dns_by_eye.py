import pytest
import json
import sys
import os

# Add the dns_by_eye directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dns_by_eye'))

from app.main import app, is_valid_domain, is_valid_dns_server

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_dns_servers_endpoint(client):
    """Test the DNS servers endpoint."""
    response = client.get('/api/dns-servers')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'dns_servers' in data
    assert 'default' in data
    assert isinstance(data['dns_servers'], list)

def test_domain_validation():
    """Test domain validation function."""
    # Valid domains
    assert is_valid_domain('example.com') == True
    assert is_valid_domain('sub.example.com') == True
    assert is_valid_domain('test-domain.org') == True
    
    # Invalid domains
    assert is_valid_domain('') == False
    assert is_valid_domain('invalid..domain') == False
    assert is_valid_domain('.invalid') == False
    assert is_valid_domain('invalid.') == False
    assert is_valid_domain('a' * 300) == False  # Too long

def test_dns_server_validation():
    """Test DNS server validation function."""
    # Valid DNS servers
    assert is_valid_dns_server('system') == True
    assert is_valid_dns_server('8.8.8.8') == True
    assert is_valid_dns_server('1.1.1.1') == True
    
    # Invalid DNS servers
    assert is_valid_dns_server('') == False
    assert is_valid_dns_server('invalid') == False
    assert is_valid_dns_server('999.999.999.999') == False

def test_trace_endpoint_invalid_domain(client):
    """Test trace endpoint with invalid domain."""
    response = client.get('/api/trace/invalid..domain')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_delegation_endpoint_missing_data(client):
    """Test delegation endpoint with missing data."""
    response = client.post('/api/delegation', 
                          json={},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_delegation_endpoint_invalid_domain(client):
    """Test delegation endpoint with invalid domain."""
    response = client.post('/api/delegation', 
                          json={'domain': 'invalid..domain'},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_compare_endpoint_invalid_data(client):
    """Test compare endpoint with invalid data."""
    response = client.post('/api/compare', 
                          json={'domains': []},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_export_endpoint_invalid_domain(client):
    """Test export endpoint with invalid domain."""
    response = client.get('/api/export/invalid..domain')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_nameservers_endpoint_invalid_domain(client):
    """Test nameservers endpoint with invalid domain."""
    response = client.get('/api/nameservers/invalid..domain')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_index_page(client):
    """Test the main index page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'DNS By Eye' in response.data

def test_static_files(client):
    """Test static file serving."""
    response = client.get('/static/dns_by_eye_200x200.png')
    # Should either return the file or 404 if it doesn't exist
    assert response.status_code in [200, 404]
