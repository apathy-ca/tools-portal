# Tools Portal

A web-based platform for hosting tools with SSL support and microservices architecture.

## Overview

Tools Portal provides a clean, scalable platform for deploying and managing multiple tools. Built with Flask, Docker, and nginx, it offers a production-ready environment with SSL certificates, security headers, and rate limiting.

## Features

- **Multi-tool Architecture**: Scalable platform for hosting multiple tools
- **SSL Support**: Automatic Let's Encrypt certificate management
- **Professional UI**: Clean, responsive interface with modern design
- **Microservices**: Docker-based containerized services
- **Security**: Rate limiting, security headers, and input validation
- **Production Ready**: Gunicorn WSGI server with nginx reverse proxy

## Current Tools

### DNS By Eye
Comprehensive DNS delegation analysis tool with visual graphs, health scoring, and glue record validation.

- **Features**: DNS delegation tracing, visual graphs, health scoring, glue record analysis
- **Access**: Available at `/dns-by-eye/` endpoint
- **Repository**: [DNS By Eye](https://github.com/apathy-ca/dns_by_eye)

### IP Whale
IP address information tool with IPv4/IPv6 detection, PTR records, ASN lookup, and NAT detection.

- **Features**: IPv4/IPv6 detection, PTR record lookup, ASN information, NAT detection, remote port detection
- **Access**: Available at `/ipwhale/` endpoint

*Additional tools are automatically detected and integrated when added to the `tools/` directory as git submodules.*

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   nginx         │    │ Tools Portal │    │   Tool Services │
│   (SSL/Proxy)   │────│   (Flask)    │────│   (Dynamic)     │
│   Port 443/80   │    │   Port 5000  │    │   Port 5001+    │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                    │
         │              ┌──────────────┐             │
         └──────────────│    Redis     │─────────────┘
                        │  (Caching)   │
                        │   Port 6379  │
                        └──────────────┘
```

Tools are dynamically detected from the `tools/` directory and automatically integrated into the platform.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Domain name with DNS pointing to your server
- Ports 80 and 443 available

### Installation

1. **Clone the repository with submodules**:
   ```bash
   git clone --recursive https://github.com/apathy-ca/tools-portal.git
   cd tools-portal
   ```
   
   Or if you already cloned without submodules:
   ```bash
   git clone https://github.com/apathy-ca/tools-portal.git
   cd tools-portal
   git submodule update --init --recursive
   ```

2. **Generate configuration files**:
   ```bash
   # Generate docker compose and nginx configuration files
   python generate-compose.py
   
   # Optional: Configure specific bind IP (see BIND_IP_CONFIGURATION.md)
   python generate-compose.py --bind-ip 192.168.1.100
   ```

3. **Configure your domain (SSL only)**:
   ```bash
   # Update nginx-tools-ssl.conf with your domain name
   sed -i 's/your-domain.com/your-actual-domain.com/g' nginx-tools-ssl.conf
   ```

4. **Deploy with SSL (Production)**:
   ```bash
   # Set up SSL certificates first
   ./scripts/setup-ssl.sh your-domain.com admin@your-domain.com
   
   # Deploy all services
   sudo docker compose -f docker compose-tools-ssl.yaml up -d
   ```

5. **Deploy without SSL (Development)**:
   ```bash
   # For local development/testing
   sudo docker compose -f docker compose-tools.yaml up -d
   ```

6. **Access the portal**:
   - **Production**: `https://your-domain.com/`
   - **Development**: `http://localhost/`
   - **Tools**: `https://your-domain.com/{tool-name}/` or `http://localhost/{tool-name}/`

## Configuration Files

### Core Files
- `app.py` - Main Flask application for tools portal
- `docker compose-tools-ssl.yaml` - Production deployment with SSL
- `nginx-tools-ssl.conf` - nginx configuration with SSL and routing
- `gunicorn_config.py` - WSGI server configuration
- `.tools-config` - Persistent configuration for bind IP and other settings

### Configuration Guides
- [`BIND_IP_CONFIGURATION.md`](BIND_IP_CONFIGURATION.md) - Configure IP binding to avoid port conflicts

### Templates
- `templates/index.html` - Main landing page
- `templates/404.html` - Error page
- `templates/500.html` - Server error page

### Static Assets
- `static/favicon.png` - Site favicon

## Adding New Tools

Tools are automatically detected and integrated when added to the `tools/` directory. See [`EXAMPLE_TOOL_INTEGRATION.md`](EXAMPLE_TOOL_INTEGRATION.md) for detailed instructions.

### Quick Process:
1. **Add tool as submodule**: `git submodule add <repo-url> tools/your-tool`
2. **Generate configuration**: `python generate-compose.py`
3. **Deploy**: `docker compose -f docker compose-tools.yaml up --build`

The system automatically:
- Detects tools with Dockerfiles in `tools/` directory
- Loads tool configuration from `config.py` if present
- Generates docker compose and nginx configurations
- Integrates tools into the portal interface

## Security Features

- **SSL/TLS**: Let's Encrypt certificates with automatic renewal
- **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- **Rate Limiting**: API and request rate limiting
- **Input Validation**: Comprehensive input sanitization
- **Container Security**: Non-root containers with minimal privileges

## Monitoring

### Health Checks
- Tools Portal: `GET /api/health`
- Individual Tools: `GET /{tool-name}/api/health`

### Logs
```bash
# View all services
sudo docker compose -f docker compose-tools-ssl.yaml logs

# View specific service
sudo docker compose -f docker compose-tools-ssl.yaml logs tools-portal
```

## Development

### Local Development
```bash
# Run without SSL for development
sudo docker compose -f docker compose-tools.yaml up -d

# Access at http://localhost/
```

### Git Submodule Management

This project uses git submodules to integrate tools while maintaining their independent repositories.

#### Working with Submodules
```bash
# Initialize submodules after cloning
git submodule update --init --recursive

# Update all submodules to latest
git submodule update --remote

# Update specific submodule
git submodule update --remote tools/dns-by-eye

# Check submodule status
git submodule status
```

#### Updating Tools
```bash
# Update DNS By Eye to latest version
cd tools/dns-by-eye
git pull origin main
cd ../..
git add tools/dns-by-eye
git commit -m "Update DNS By Eye submodule to latest version"
git push origin main
```

### Adding New Tools

Tools are automatically detected and integrated. See [`EXAMPLE_TOOL_INTEGRATION.md`](EXAMPLE_TOOL_INTEGRATION.md) for complete instructions.

**Quick Steps:**
1. **Add tool as submodule**:
   ```bash
   git submodule add https://github.com/your-org/your-tool.git tools/your-tool
   ```

2. **Generate configuration**:
   ```bash
   python generate-compose.py
   ```

3. **Deploy**:
   ```bash
   docker compose -f docker compose-tools.yaml up --build
   ```

**Tool Requirements:**
- Must have a `Dockerfile` in the tool directory
- Should include `config.py` with `TOOL_INFO` for proper integration
- Must provide `/api/health` endpoint on port 5000

The system automatically generates docker compose files, nginx routing, and portal integration.

## Production Deployment

### SSL Certificate Management
Certificates are automatically managed by Let's Encrypt. Manual renewal:
```bash
sudo docker compose -f docker compose-tools-ssl.yaml exec nginx certbot renew
```

### Backup
Important files to backup:
- SSL certificates: `/etc/letsencrypt/`
- Configuration files: `*.yaml`, `*.conf`
- Tool data: Tool-specific data directories

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
sudo docker compose -f docker compose-tools-ssl.yaml up -d --build
```

## API Documentation

### Tools Portal API
- `GET /api/health` - Health check
- `GET /api/tools` - List available tools

### Tool-Specific APIs
Each tool provides its own API endpoints under its namespace (e.g., `/dns-by-eye/api/`).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/apathy-ca/tools-portal/issues)
- **Documentation**: This README and inline code comments
- **Community**: GitHub Discussions

## Changelog

### v1.0.0
- Initial release with DNS By Eye integration
- SSL support with Let's Encrypt
- Microservices architecture
- Professional landing page
- Security features and rate limiting

---

**Tools Portal** - General-purpose tools platform
