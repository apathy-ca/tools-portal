# DNS By Eye

**Version 1.0.0**

DNS By Eye is a Flask-based DNS delegation visualizer. It traces DNS delegation chains from the root through TLDs to the authoritative nameservers, then renders interactive graphs of each layer and cross-reference diagrams. Features include:

- **Multi-domain comparison**: Compare DNS delegation paths across multiple domains
- **Response time monitoring**: Track DNS query performance with slow response indicators
- **Interactive visualizations**: Graphviz-based PNG diagrams for each delegation layer
- **Cross-reference analysis**: Detailed analysis of nameserver relationships and consistency
- **Comprehensive API**: RESTful endpoints for programmatic access
- **Export capabilities**: JSON and CSV export formats
- **URL sharing**: Shareable URLs with query parameters for easy collaboration
- **Multiple DNS servers**: Support for various public DNS resolvers
- **Debug mode**: Detailed timing and performance analysis
- **Rate limiting**: Built-in protection against abuse
- **Modern UI**: Clean, responsive interface with syntax highlighting

## Features

### Core Functionality
- Trace delegation chain with optional verbose glue records
- Graphviz-based PNG diagrams for each delegation layer
- Cross-reference graph of last-level nameservers
- Response time tracking with slow query detection
- Multi-domain comparison analysis

### Technical Features
- In-memory caching (Flask-Caching) with configurable TTL
- Rate limiting (Flask-Limiter) to prevent abuse
- Configurable timeouts for DNS resolution
- Content Security Policy header for security hardening
- Dockerfile and Gunicorn for production deployment
- Comprehensive API documentation

## Live Demo

Try DNS By Eye online at: **[http://tools.apathy.ca:5000](http://tools.apathy.ca:5000)**

## Quickstart (Docker)

```bash
git clone https://github.com/apathy-ca/dns_by_eye.git
cd dns_by_eye
docker build -t dns_by_eye .
docker run --rm -p 5000:5000 dns_by_eye
```

Open http://localhost:5000 in your browser.

## Docker Compose

### Basic Setup (HTTP only)

```bash
# Start the application with Redis
docker compose up

# Start in detached mode
docker compose up -d

# Rebuild images after code changes
docker compose up --build

# Stop the application
docker compose down
```

### SSL Setup with Let's Encrypt

For production deployment with SSL certificates:

```bash
# Set up SSL certificates (replace with your domain and email)
# This runs as a daemon - you can close the terminal after setup
./setup-ssl.sh your-domain.com admin@your-domain.com

# Or without email (not recommended for production)
./setup-ssl.sh your-domain.com

# Management commands (after setup):
docker compose -f docker-compose.ssl.yaml ps              # Check status
docker compose -f docker-compose.ssl.yaml logs -f         # View logs (Ctrl+C to exit)
docker compose -f docker-compose.ssl.yaml exec certbot certbot certificates  # Check certificates
docker compose -f docker-compose.ssl.yaml down            # Stop all services
docker compose -f docker-compose.ssl.yaml restart         # Restart all services

# Troubleshooting SSL issues:
./troubleshoot-ssl.sh your-domain.com                     # Comprehensive SSL diagnostics
```

The SSL setup includes:
- **Nginx reverse proxy** with SSL termination
- **Let's Encrypt certificates** with automatic renewal
- **Security headers** and HTTPS redirects
- **Rate limiting** for API protection
- **Gzip compression** for better performance

**Important**: 
- After making code changes, use `docker compose up --build` to rebuild the Docker image
- For SSL setup, ensure your domain points to your server before running the setup script
- Certificates are automatically renewed every 12 hours

## API Endpoints

### Full Delegation Analysis
```http
POST /api/delegation
Content-Type: application/json

{
  "domain": "example.com",
  "verbose": true,
  "dns_server": "system"
}
```

### Simple Trace (No Visualizations)
```http
GET /api/trace/example.com?verbose=true&dns_server=8.8.8.8
```

### Multi-Domain Comparison
```http
POST /api/compare
Content-Type: application/json

{
  "domains": ["example.com", "google.com"],
  "verbose": false,
  "dns_server": "1.1.1.1"
}
```

### Export Data
```http
GET /api/export/example.com?format=json&verbose=true
GET /api/export/example.com?format=csv&verbose=true
```

### Debug Analysis
```http
GET /api/debug/example.com?verbose=true&dns_server=8.8.8.8
```

### Utility Endpoints
```http
GET /api/nameservers/example.com?dns_server=1.1.1.1
GET /api/dns-servers
GET /api/health
```

## Response Format

All endpoints return JSON with comprehensive data:

- `trace`: Array of delegation steps with zones, nameservers, response times
- `graph_urls`: URLs of generated visualization graphs
- `chain`: Human-readable delegation chain
- `cross_ref_results`: Nameserver consistency analysis
- `cross_ref_graph_url`: Cross-reference visualization
- `timing_info`: Performance metrics (debug mode)

## Supported DNS Servers

- **system**: System default DNS resolver
- **8.8.8.8**: Google DNS
- **1.1.1.1**: Cloudflare DNS
- **9.9.9.9**: Quad9 DNS
- **208.67.222.222**: OpenDNS

## Configuration

All settings can be overridden via environment variables or `config.py`:

```python
DNS_TIMEOUT = 3          # Individual query timeout
DNS_LIFETIME = 6         # Total resolution timeout
RATELIMIT_DEFAULT = "100 per day"
CACHE_DEFAULT_TIMEOUT = 300
```

## Development

### Local Development
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m flask run
```

### Testing
```bash
pytest tests/
```

## License

This project is open source. See LICENSE file for details.

## Links

- **Live Demo**: [http://tools.apathy.ca:5000](http://tools.apathy.ca:5000)
- **GitHub Repository**: [https://github.com/apathy-ca/dns_by_eye](https://github.com/apathy-ca/dns_by_eye)

## Acknowledgments

Inspired by [dnsbajaj](https://www.zonecut.net/dns/) | Created with ChatGPT, Cline & Anthropic (Claude Sonnet)
