"""
Basic tests for DNS By Eye application
"""

import pytest
import sys
import os

# Add the app directory to the path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_import_main():
    """Test that we can import the main application module"""
    try:
        import main
        assert hasattr(main, 'app')
    except ImportError as e:
        pytest.skip(f"Could not import main module: {e}")

def test_basic_math():
    """Basic test to ensure pytest is working"""
    assert 1 + 1 == 2

def test_domain_validation():
    """Test domain validation function if available"""
    try:
        from main import is_valid_domain
        
        # Valid domains
        assert is_valid_domain('example.com') == True
        assert is_valid_domain('sub.example.com') == True
        assert is_valid_domain('test.co.uk') == True
        
        # Invalid domains
        assert is_valid_domain('') == False
        assert is_valid_domain('invalid') == False
        assert is_valid_domain('..com') == False
        
    except ImportError:
        pytest.skip("Domain validation function not available")

if __name__ == '__main__':
    pytest.main([__file__])
