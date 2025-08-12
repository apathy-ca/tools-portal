#!/usr/bin/env python3
"""
Simplified test script to demonstrate the resilient DNS tracing functionality.
This script tests the core DNS logic without Flask dependencies.
"""

import dns.resolver
import time
import re

# DNS configuration
DNS_TIMEOUT = 2.0
DNS_LIFETIME = 4.0

# Configure DNS resolver with timeouts
resolver = dns.resolver.Resolver()
resolver.timeout = DNS_TIMEOUT
resolver.lifetime = DNS_LIFETIME

DOMAIN_REGEX = re.compile(r'^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$')

def is_valid_domain(domain):
    return bool(DOMAIN_REGEX.match(domain.strip('.')))

def trace_delegation_core(domain, verbose=False, debug=False):
    """
    Core DNS delegation tracing function - resilient version.
    This is the same logic as in main.py but without Flask dependencies.
    """
    query_resolver = resolver
    
    result = []
    timing_info = {}
    labels = [label for label in domain.strip('.').split('.') if label]
    # Reverse labels for right-to-left processing
    reversed_labels = labels[::-1]
    chain = ['.']
    # Build chain from root to domain
    for i in range(len(reversed_labels)):
        zone = '.'.join(reversed_labels[:i+1][::-1])
        chain.append(zone)

    # Track if we've encountered a fatal error that should stop further tracing
    should_continue = True
    
    for i in range(len(chain)):
        if not should_continue:
            break
            
        zone = chain[i]
        start_time = time.time()
        error_type = None
        
        try:
            ns_records = query_resolver.resolve(zone, 'NS')
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
            ns_list = [r.to_text() for r in ns_records]
            verbose_info = ""
            
            if verbose:
                glue = []
                for ns in ns_list:
                    try:
                        a_start = time.time()
                        a_records = query_resolver.resolve(ns, 'A')
                        a_end = time.time()
                        a_time = round((a_end - a_start) * 1000, 2)
                        glue.append(f"{ns} A: {', '.join([a.to_text() for a in a_records])} ({a_time}ms)")
                    except Exception:
                        pass
                    try:
                        aaaa_start = time.time()
                        aaaa_records = query_resolver.resolve(ns, 'AAAA')
                        aaaa_end = time.time()
                        aaaa_time = round((aaaa_end - aaaa_start) * 1000, 2)
                        glue.append(f"{ns} AAAA: {', '.join([a.to_text() for a in aaaa_records])} ({aaaa_time}ms)")
                    except Exception:
                        pass
                if glue:
                    verbose_info = " | ".join(glue)
                    
        except dns.resolver.NXDOMAIN as e:
            # Domain doesn't exist - this is a definitive answer, stop here
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"NXDOMAIN: {zone} does not exist"]
            verbose_info = f"Domain {zone} does not exist" if verbose else ""
            error_type = "NXDOMAIN"
            should_continue = False
            
        except dns.resolver.NoAnswer as e:
            # No NS records found for this zone
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"No NS records: {zone} has no nameservers"]
            verbose_info = f"No NS records found for {zone}" if verbose else ""
            error_type = "NO_NS"
            should_continue = False
            
        except dns.resolver.Timeout as e:
            # Timeout - could be temporary, but stop tracing deeper
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"Timeout: Query for {zone} timed out"]
            verbose_info = f"DNS query timeout for {zone}" if verbose else ""
            error_type = "TIMEOUT"
            should_continue = False
            
        except dns.resolver.NoNameservers as e:
            # No nameservers available to answer the query
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"No nameservers: No servers available for {zone}"]
            verbose_info = f"No nameservers available for {zone}" if verbose else ""
            error_type = "NO_NAMESERVERS"
            should_continue = False
            
        except Exception as e:
            # Other errors - log them but continue if it's not too deep in the chain
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            error_msg = str(e)
            ns_list = [f"Error: {error_msg}"]
            verbose_info = f"Query error for {zone}: {error_msg}" if verbose else ""
            error_type = "OTHER"
            
            # If we're past the TLD level and getting errors, stop tracing
            if i > 1:  # 0=root, 1=TLD, 2+=domain levels
                should_continue = False
        
        # Flag slow responses (>2000ms is considered slow for DNS)
        is_slow = response_time > 2000
        timing_info[zone] = {
            'response_time': response_time, 
            'is_slow': is_slow,
            'error_type': error_type
        }
        
        result.append({
            'zone': zone, 
            'nameservers': ns_list, 
            'verbose': verbose_info if verbose else None,
            'response_time': response_time,
            'is_slow': is_slow,
            'error_type': error_type,
            'trace_stopped': not should_continue and i < len(chain) - 1
        })
    
    # If we stopped early, update the chain to reflect what was actually traced
    if not should_continue and len(result) < len(chain):
        chain = chain[:len(result)]
    
    return result, chain, timing_info if debug else {}

def test_domain(domain, description):
    """Test a domain and print the results."""
    print(f"\n{'='*60}")
    print(f"Testing: {domain}")
    print(f"Description: {description}")
    print(f"{'='*60}")
    
    try:
        trace, chain, timing = trace_delegation_core(domain, verbose=True, debug=True)
        
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
    print("DNS By Eye - Resilient DNS Tracing Test (Core Logic)")
    print("This script tests how the core DNS logic handles various failure scenarios.")
    
    # Test cases
    test_cases = [
        ("google.com", "Valid domain - should work normally"),
        ("nonexistent-domain-12345.com", "Non-existent domain - should show NXDOMAIN"),
        ("test.nonexistent-tld-12345", "Non-existent TLD - should fail at TLD level"),
        ("subdomain.nonexistent-domain-12345.com", "Subdomain of non-existent domain"),
    ]
    
    for domain, description in test_cases:
        test_domain(domain, description)
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print("The core DNS logic now handles failures gracefully,")
    print("tracing as far as possible and stopping when it encounters")
    print("unresolvable zones instead of failing completely.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
