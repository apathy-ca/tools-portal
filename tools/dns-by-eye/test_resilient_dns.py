#!/usr/bin/env python3
"""
Test script to demonstrate the resilient DNS tracing functionality.
This script tests various failure scenarios to show how the application
now handles non-existent domains gracefully.
"""

import sys
import os
import json

# Add the app directory to the path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from main import trace_delegation, create_custom_resolver

def test_domain(domain, description):
    """Test a domain and print the results."""
    print(f"\n{'='*60}")
    print(f"Testing: {domain}")
    print(f"Description: {description}")
    print(f"{'='*60}")
    
    try:
        trace, chain, timing = trace_delegation(domain, verbose=True, debug=True)
        
        print(f"Chain: {' → '.join(chain)}")
        print(f"Trace completed with {len(trace)} steps")
        
        for i, step in enumerate(trace):
            print(f"\nStep {i+1}: {step['zone']}")
            print(f"  Response time: {step['response_time']}ms")
            print(f"  Error type: {step.get('error_type', 'None')}")
            print(f"  Trace stopped: {step.get('trace_stopped', False)}")
            print(f"  Nameservers:")
            for ns in step['nameservers']:
                print(f"    - {ns}")
            if step.get('verbose'):
                print(f"  Verbose info: {step['verbose']}")
        
        # Check if we have timing info
        if timing:
            print(f"\nTiming details:")
            for zone, info in timing.items():
                print(f"  {zone}: {info['response_time']}ms (error: {info.get('error_type', 'None')})")
                
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    """Run tests for various domain scenarios."""
    print("DNS By Eye - Resilient DNS Tracing Test")
    print("This script tests how the application handles various DNS failure scenarios.")
    
    # Test cases
    test_cases = [
        ("google.com", "Valid domain - should work normally"),
        ("nonexistent-domain-12345.com", "Non-existent domain - should show NXDOMAIN"),
        ("test.nonexistent-tld-12345", "Non-existent TLD - should fail at TLD level"),
        ("subdomain.nonexistent-domain-12345.com", "Subdomain of non-existent domain"),
        ("example.com", "Valid domain - should work normally"),
    ]
    
    for domain, description in test_cases:
        test_domain(domain, description)
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print("The application should now handle DNS failures gracefully,")
    print("tracing as far as possible and stopping when it encounters")
    print("unresolvable zones instead of failing completely.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
