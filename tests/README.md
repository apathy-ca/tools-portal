# Tools Portal Tests

## Overview

This directory contains unit tests for the Tools Portal application.

## Running Tests

### Using unittest (built-in)

```bash
# Run all tests
python -m unittest discover tests

# Run with verbose output
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_app
```

### Using pytest (recommended)

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_app.py::ToolsPortalTestCase::test_health_endpoint
```

## Test Coverage

Current test coverage includes:

### API Endpoints
- ✅ `GET /health` - Basic health check
- ✅ `GET /api/tools` - Tools list API
- ✅ `GET /api/health/detailed` - Detailed health check
- ✅ `GET /` - Main landing page

### Functionality
- ✅ Caching behavior for `/api/tools`
- ✅ Caching behavior for `/api/health/detailed`
- ✅ Dynamic tool discovery
- ✅ 404 error handling
- ✅ Static file serving
- ✅ Tool configuration structure

## Adding New Tests

When adding new functionality:

1. Create test methods in `test_app.py`
2. Follow naming convention: `test_<functionality>`
3. Use descriptive docstrings
4. Test both success and failure cases
5. Clear cache in `setUp()` to avoid test interdependencies

Example:

```python
def test_new_feature(self):
    """Test new feature works correctly."""
    response = self.client.get('/new-endpoint')
    self.assertEqual(response.status_code, 200)
    # Add more assertions
```

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=app --cov-report=xml
```
