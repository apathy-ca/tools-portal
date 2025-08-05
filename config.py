import os

class Config:
    # Caching configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))

    # DNS resolver timeouts
    DNS_TIMEOUT = float(os.environ.get('DNS_TIMEOUT', '2'))
    DNS_LIFETIME = float(os.environ.get('DNS_LIFETIME', '4'))

    # Rate limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '10 per minute')
