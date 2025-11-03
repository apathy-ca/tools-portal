"""
Basic unit tests for Tools Portal
"""

import unittest
import json
from app import app, cache, TOOLS


class ToolsPortalTestCase(unittest.TestCase):
    """Test cases for Tools Portal application."""

    def setUp(self):
        """Set up test client and clear cache before each test."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        cache.clear()

    def tearDown(self):
        """Clean up after each test."""
        cache.clear()

    def test_health_endpoint(self):
        """Test basic health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'tools-portal')
        self.assertIn('timestamp', data)
        self.assertIn('tools_available', data)

    def test_tools_api_endpoint(self):
        """Test tools list API endpoint."""
        response = self.client.get('/api/tools')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('tools', data)
        self.assertIn('categories', data)
        self.assertIn('total_tools', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['total_tools'], len(TOOLS))

    def test_tools_api_caching(self):
        """Test that tools API endpoint is cached."""
        # First request
        response1 = self.client.get('/api/tools')
        data1 = json.loads(response1.data)
        timestamp1 = data1['timestamp']

        # Second request should return cached response with same timestamp
        response2 = self.client.get('/api/tools')
        data2 = json.loads(response2.data)
        timestamp2 = data2['timestamp']

        self.assertEqual(timestamp1, timestamp2,
                        "Cached response should have same timestamp")

    def test_index_page(self):
        """Test main landing page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tools Portal', response.data)

    def test_404_handler(self):
        """Test custom 404 error page."""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)

    def test_static_files(self):
        """Test static file serving."""
        response = self.client.get('/static/favicon.png')
        # Should either return the file (200) or not found (404)
        self.assertIn(response.status_code, [200, 404])

    def test_detailed_health_structure(self):
        """Test detailed health endpoint structure."""
        response = self.client.get('/api/health/detailed')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
        self.assertIn('service', data)
        self.assertIn('dependencies', data)
        self.assertIn('metrics', data)

    def test_detailed_health_caching(self):
        """Test that detailed health endpoint is cached."""
        # First request
        response1 = self.client.get('/api/health/detailed')
        data1 = json.loads(response1.data)
        timestamp1 = data1['timestamp']

        # Second request within cache timeout should have same timestamp
        response2 = self.client.get('/api/health/detailed')
        data2 = json.loads(response2.data)
        timestamp2 = data2['timestamp']

        self.assertEqual(timestamp1, timestamp2,
                        "Cached response should have same timestamp")


class DynamicToolDiscoveryTestCase(unittest.TestCase):
    """Test cases for dynamic tool discovery."""

    def test_tools_detected(self):
        """Test that tools are detected on startup."""
        self.assertIsInstance(TOOLS, dict)
        self.assertGreater(len(TOOLS), 0, "At least one tool should be detected")

    def test_tool_structure(self):
        """Test that detected tools have required fields."""
        for tool_name, tool_config in TOOLS.items():
            self.assertIn('name', tool_config)
            self.assertIn('description', tool_config)
            self.assertIn('version', tool_config)
            self.assertIn('url', tool_config)
            self.assertIn('category', tool_config)
            self.assertIn('status', tool_config)


if __name__ == '__main__':
    unittest.main()
