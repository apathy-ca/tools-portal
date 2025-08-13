# IPWhale 🐋

IPWhale is an IP address information tool inspired by [ipquail.com](https://ipquail.com) and [ipchicken.com](https://ipchicken.com). It provides comprehensive information about your IP address, including IPv4/IPv6 detection, PTR records, ASN information, and NAT detection.

## Features

### Core Functionality (IPQuail-inspired)
- **IPv4 and IPv6 Detection**: Automatically detects and displays both IPv4 and IPv6 addresses
- **PTR Record Lookup**: Reverse DNS lookups for both IP versions
- **ASN Information**: Autonomous System Number detection using DNS-based lookups
- **Curl-friendly API**: Shell scriptable endpoints for automation

### Advanced Features (IPChicken-inspired)
- **Remote Port Detection**: Shows the source port of your connection
- **User Agent Display**: Full browser/client identification
- **NAT Detection**: Identifies if you're behind NAT/proxy by analyzing multiple IP sources

### API Endpoints

#### Curl-friendly Endpoints
```bash
# Get IPv4 address
curl -s your-domain.com/api/4/ip

# Get IPv6 address  
curl -s your-domain.com/api/6/ip

# Get IPv4 PTR record
curl -s your-domain.com/api/4/ptr

# Get IPv6 PTR record
curl -s your-domain.com/api/6/ptr

# Get IPv4 ASN
curl -s your-domain.com/api/4/asn

# Get IPv6 ASN
curl -s your-domain.com/api/6/asn
```

#### JSON API Endpoints
- `/api/ip` - Basic IP information
- `/api/full` - Comprehensive client information including NAT detection
- `/api/health` - Health check endpoint

## Installation

### Standalone Docker Container

```bash
# Build the container
docker build -t ipwhale .

# Run the container
docker run -p 5000:5000 ipwhale
```

### Integration with Tools-Portal

IPWhale is designed to integrate seamlessly with the tools-portal framework:

1. Copy the ipwhale directory to `tools-portal/tools/`
2. Update the tools-portal configuration to include ipwhale
3. Use docker-compose to deploy the integrated system

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app/main.py
```

## Technical Details

### NAT Detection
IPWhale detects NAT/proxy scenarios by comparing:
- `request.remote_addr` (direct connection IP)
- `X-Forwarded-For` header (proxy chain)
- `X-Real-IP` header (load balancer real IP)

When multiple IP sources are detected, it indicates the client is behind NAT or a proxy.

### ASN Lookup
ASN information is retrieved using DNS-based lookups:
- IPv4: `origin.asn.cymru.com`
- IPv6: `origin6.asn.cymru.com`

### Security Features
- Comprehensive security headers (CSP, HSTS, etc.)
- Input validation and sanitization
- Rate limiting ready (disabled by default for better UX)
- Non-root container execution
- Structured error handling

## Configuration

Environment variables:
- `DEBUG`: Enable debug mode (default: false)
- `DNS_TIMEOUT`: DNS query timeout in seconds (default: 5.0)
- `DNS_LIFETIME`: DNS resolver lifetime (default: 10.0)
- `LOG_LEVEL`: Logging level (default: INFO)
- `STATIC_URL_PATH`: Static files URL path for integration

## Example Output

### Web Interface
```
IP Whale!
This website will tell you your IP[v4|v6] addresses.

Your IPv6 address is: None
Your IPv4 address is: 203.0.113.42
Your IPv6 PTR is: None  
Your IPv4 PTR is: example.isp.com
Your IPv6 source ASN is: None
Your IPv4 source ASN is: 64512
```

### Curl Output
```bash
$ curl -s localhost:5000/api/4/ip
203.0.113.42

$ curl -s localhost:5000/api/4/ptr  
example.isp.com

$ curl -s localhost:5000/api/4/asn
64512
```

## License

This project follows the same license as the tools-portal framework.

## Contributing

IPWhale is part of the tools-portal ecosystem. Contributions should follow the established patterns and coding standards of the framework.

## Version History

- **v1.0.0**: Initial release with full IPQuail and IPChicken functionality
  - IPv4/IPv6 detection and PTR lookups
  - ASN information via DNS
  - NAT detection capabilities
  - Curl-friendly API endpoints
  - Tools-portal integration ready
