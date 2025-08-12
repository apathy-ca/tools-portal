# DNS By Eye

**Version 1.0.2**

DNS By Eye is a Flask-based DNS delegation visualizer. It traces DNS delegation chains from the root through TLDs to the authoritative nameservers, then renders interactive graphs of each layer and cross-reference diagrams. Features include:

- **Layered health scoring**: Domain-focused health assessment with 1 point per delegation layer plus bonuses
- **Smart graph condensation**: Large nameserver sets (4+) show first 3 + "X more" for cleaner visuals
- **Resilient DNS tracing**: Gracefully handles broken nameservers and non-existent domains
- **Intelligent glue analysis**: Ignores "unnecessary" glue records while flagging serious issues
- **Multi-domain comparison**: Compare DNS delegation paths across multiple domains
- **Response time monitoring**: Track DNS query performance with slow response indicators
- **Interactive visualizations**: Graphviz-based PNG diagrams for each delegation layer
- **Cross-reference analysis**: Detailed analysis of nameserver relationships and consistency
- **Error visualization**: Visual indicators for broken nameservers and DNS failures
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

### Resilient DNS Tracing (New in v1.0.1)
- **Graceful error handling**: Continues tracing as far as possible when encountering DNS failures
- **Specific error detection**: Distinguishes between NXDOMAIN, timeouts, and other DNS errors
- **Visual error indicators**: Red error nodes in graphs show broken nameservers and DNS issues
- **Partial results**: Provides useful information even when some nameservers are unreachable
- **Broken nameserver support**: Handles misconfigured nameservers without complete failure
- **Enhanced cross-reference analysis**: Color-coded nameservers based on reachability status

### Glue Record Validation (New Feature)
- **Comprehensive glue record analysis**: Checks glue records across the entire delegation chain
- **In-zone vs out-of-zone detection**: Identifies when glue records are expected vs unnecessary
- **Glue record consistency**: Verifies that glue records match actual DNS resolution
- **Missing glue detection**: Identifies missing glue records for in-zone nameservers
- **Unnecessary glue detection**: Flags unnecessary glue records for out-of-zone nameservers
- **Additional section parsing**: Analyzes DNS response additional sections for glue records
- **Visual glue record reporting**: Detailed UI display of glue record status and issues

### Technical Features
- In-memory caching (Flask-Caching) with configurable TTL
- Rate limiting (Flask-Limiter) to prevent abuse
- Configurable timeouts for DNS resolution
- Content Security Policy header for security hardening
- Dockerfile and Gunicorn for production deployment
- Comprehensive API documentation

## Live Demo

Try DNS By Eye online at: **[https://tools.apathy.ca](https://tools.apathy.ca)**

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
./setup-ssl.sh your-domain.com admin@your-domain.com

# Or without email (not recommended for production)
./setup-ssl.sh your-domain.com

# Management commands (after setup):
docker compose -f docker-compose.ssl.yaml ps              # Check status
docker compose -f docker-compose.ssl.yaml logs -f         # View logs (Ctrl+C to exit)
docker compose -f docker-compose.ssl.yaml exec certbot certbot certificates  # Check certificates
docker compose -f docker-compose.ssl.yaml down            # Stop all services
docker compose -f docker-compose.ssl.yaml restart         # Restart all services

# Troubleshooting issues:
./scripts/troubleshoot.sh your-domain.com                 # Comprehensive diagnostics
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

### Updating Existing Deployments

If you have an existing DNS By Eye deployment and want to update to the latest version:

```bash
# 1. Pull the latest code
git pull origin main

# 2. Update nginx configuration (this fixes static file serving issues)
docker compose -f docker-compose.ssl.yaml restart nginx

# 3. If graphs still don't load, restart all services
docker compose -f docker-compose.ssl.yaml restart

# 4. Optional: Clean up old generated files
./scripts/cleanup-generated.sh

# 5. Verify the update worked
curl -I https://your-domain.com/static/dns_by_eye_favicon.png
```

**Note**: Recent updates fixed an issue where generated graph images were returning 404 errors. The nginx configuration now properly routes all static file requests to the Flask application.

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

### Example: Analyzing the Broken Test Domain
Try the intentionally broken `test.apathy.ca` domain to see DNS By Eye's error handling capabilities:

```bash
# Analyze the broken test domain with verbose output
curl -X POST "https://tools.apathy.ca/api/delegation" \
     -H "Content-Type: application/json" \
     -d '{
       "domain": "test.apathy.ca",
       "verbose": true,
       "dns_server": "system"
     }'

# Simple trace without visualizations
curl "https://tools.apathy.ca/api/trace/test.apathy.ca?verbose=true&dns_server=8.8.8.8"

# Compare broken domain with a working one
curl -X POST "https://tools.apathy.ca/api/compare" \
     -H "Content-Type: application/json" \
     -d '{
       "domains": ["test.apathy.ca", "google.com"],
       "verbose": true,
       "dns_server": "1.1.1.1"
     }'
```

This will demonstrate:
- **Broken nameserver detection** (ns3.broken.example)
- **Timeout handling** for unresponsive servers
- **Visual error indicators** in generated graphs
- **Partial delegation results** despite DNS failures

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

### Glue Record Analysis
```http
GET /api/glue-records/example.com?dns_server=8.8.8.8
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

## Utility Scripts

The project includes several utility scripts in the `scripts/` directory:

- **`scripts/setup-ssl.sh`**: Generic SSL setup script for any domain
- **`scripts/troubleshoot.sh`**: Comprehensive troubleshooting and diagnostics
- **`scripts/cleanup-generated.sh`**: Clean up old generated graph files to manage disk space

For backward compatibility, `setup-ssl.sh` in the root directory links to the new script.

### Usage Examples
```bash
# SSL setup with email notifications
./scripts/setup-ssl.sh example.com admin@example.com

# Basic troubleshooting
./scripts/troubleshoot.sh

# Troubleshooting with domain-specific SSL checks
./scripts/troubleshoot.sh example.com

# Clean up generated files older than 7 days (default)
./scripts/cleanup-generated.sh

# Clean up files older than 3 days
./scripts/cleanup-generated.sh -d 3

# Clean up if total size exceeds 500MB
./scripts/cleanup-generated.sh -s 500M

# Force cleanup without confirmation
./scripts/cleanup-generated.sh -d 1 -f
```

### Maintenance

**Generated Files Cleanup**: The application generates PNG graph files in `app/static/generated/` for each DNS analysis. 

**Automatic Cleanup**: By default, both Docker Compose configurations include a cleanup service that automatically deletes generated files older than 1 day every 24 hours. This runs out of the box with no configuration needed.

**Manual Cleanup**: You can also run cleanup manually using the script:

```bash
# Manual cleanup (files older than 7 days by default)
./scripts/cleanup-generated.sh

# Custom cleanup options
./scripts/cleanup-generated.sh -d 3    # Files older than 3 days
./scripts/cleanup-generated.sh -s 500M # If total size > 500MB
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is one of the most permissive open source licenses, allowing you to use, modify, distribute, and sell this software for any purpose without limitation.

## Links

- **Live Demo**: [https://tools.apathy.ca](https://tools.apathy.ca)
- **GitHub Repository**: [https://github.com/apathy-ca/dns_by_eye](https://github.com/apathy-ca/dns_by_eye)

## LLM-Powered Development

This project serves as a comprehensive example of **100% LLM-assisted software development**. Every line of code, documentation, configuration, and feature was developed through collaboration with Large Language Models, demonstrating the current capabilities of AI-assisted programming.

### Development Approach
- **Primary Development**: ChatGPT (GPT-4) for initial architecture, core functionality, and major features
- **Code Refinement**: Anthropic Claude (via Cline) for debugging, optimization, and advanced features
- **Iterative Enhancement**: Continuous collaboration between human direction and AI implementation

### Development Costs
- **ChatGPT (GPT-4)**: < $1.00 USD total
- **Claude Sonnet (via Cline)**: $29.27 USD total
- **Total Project Cost**: $30.27 USD

This demonstrates that sophisticated, production-ready applications can be developed cost-effectively using modern LLMs, with total development costs remaining well under typical hourly consulting rates.

### Key Insights
- **Rapid Prototyping**: From concept to working application in hours rather than days
- **Comprehensive Documentation**: AI naturally generates thorough documentation alongside code
- **Best Practices**: LLMs incorporate modern development practices (Docker, testing, security)
- **Problem Solving**: Effective debugging and optimization through AI collaboration
- **Feature Completeness**: Full-featured application with API, UI, deployment, and monitoring

## Acknowledgments

Inspired by [dnsbajaj](https://www.zonecut.net/dns/) | Created with ChatGPT, Cline & Anthropic (Claude Sonnet)
