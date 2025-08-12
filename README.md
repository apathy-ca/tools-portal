# Tools Portal

A professional web-based platform for hosting network administration tools with SSL support and microservices architecture.

## Overview

Tools Portal provides a clean, scalable platform for deploying and managing multiple network administration tools. Built with Flask, Docker, and nginx, it offers a production-ready environment with SSL certificates, security headers, and rate limiting.

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

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   nginx         │    │ Tools Portal │    │   DNS By Eye    │
│   (SSL/Proxy)   │────│   (Flask)    │────│    (Flask)      │
│   Port 443/80   │    │   Port 5000  │    │   Port 5001     │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                    │
         │              ┌──────────────┐             │
         └──────────────│    Redis     │─────────────┘
                        │  (Caching)   │
                        │   Port 6379  │
                        └──────────────┘
```

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

2. **Configure your domain**:
   ```bash
   # Update nginx-tools-ssl.conf with your domain name
   sed -i 's/tools.apathy.ca/your-domain.com/g' nginx-tools-ssl.conf
   ```

3. **Deploy with SSL (Production)**:
   ```bash
   # Set up SSL certificates first
   ./scripts/setup-ssl.sh your-domain.com admin@your-domain.com
   
   # Deploy all services
   sudo docker compose -f docker-compose-tools-ssl.yaml up -d
   ```

4. **Deploy without SSL (Development)**:
   ```bash
   # For local development/testing
   sudo docker compose -f docker-compose-tools.yaml up -d
   ```

5. **Access the portal**:
   - **Production**: `https://your-domain.com/`
   - **Development**: `http://localhost/`
   - **DNS By Eye**: `https://your-domain.com/dns-by-eye/` or `http://localhost/dns-by-eye/`

## Configuration Files

### Core Files
- `app.py` - Main Flask application for tools portal
- `docker-compose-tools-ssl.yaml` - Production deployment with SSL
- `nginx-tools-ssl.conf` - nginx configuration with SSL and routing
- `gunicorn_config.py` - WSGI server configuration

### Templates
- `templates/index.html` - Main landing page
- `templates/404.html` - Error page
- `templates/500.html` - Server error page

### Static Assets
- `static/favicon.png` - Site favicon

## Adding New Tools

To add a new tool to the platform:

1. **Create tool directory**: Add your tool in a subdirectory
2. **Update docker-compose**: Add service configuration
3. **Update nginx config**: Add routing rules
4. **Update landing page**: Add tool to `templates/index.html`

Example service addition:
```yaml
your-tool:
  build: ./tools/your-tool
  container_name: your-tool
  restart: unless-stopped
  networks:
    - tools-network
  depends_on:
    - redis
```

## Security Features

- **SSL/TLS**: Let's Encrypt certificates with automatic renewal
- **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- **Rate Limiting**: API and request rate limiting
- **Input Validation**: Comprehensive input sanitization
- **Container Security**: Non-root containers with minimal privileges

## Monitoring

### Health Checks
- Tools Portal: `GET /api/health`
- DNS By Eye: `GET /dns-by-eye/api/health`

### Logs
```bash
# View all services
sudo docker compose -f docker-compose-tools-ssl.yaml logs

# View specific service
sudo docker compose -f docker-compose-tools-ssl.yaml logs tools-portal
```

## Development

### Local Development
```bash
# Run without SSL for development
sudo docker compose -f docker-compose-tools.yaml up -d

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

To add a new tool as a submodule:

1. **Add the tool as a submodule**:
   ```bash
   git submodule add https://github.com/your-org/your-tool.git tools/your-tool
   ```

2. **Update docker-compose configuration**:
   ```yaml
   your-tool:
     build:
       context: ./tools/your-tool
       dockerfile: Dockerfile
     container_name: your-tool
     restart: unless-stopped
     networks:
       - tools-network
     depends_on:
       - redis
   ```

3. **Update nginx routing** in `nginx-tools-ssl.conf`:
   ```nginx
   # Your Tool
   location /your-tool/ {
       limit_req zone=general burst=20 nodelay;
       rewrite ^/your-tool/(.*)$ /$1 break;
       proxy_pass http://your_tool;
       # ... proxy headers
   }
   ```

4. **Update tool registry** in `app.py`:
   ```python
   TOOLS = {
       'your-tool': {
           'name': 'Your Tool',
           'description': 'Description of your tool',
           'version': '1.0.0',
           'url': '/your-tool/',
           'icon': '🔧',
           'category': 'System Administration',
           'status': 'stable'
       }
   }
   ```

5. **Commit the integration**:
   ```bash
   git add .
   git commit -m "Add Your Tool as submodule"
   git push origin main
   ```

## Production Deployment

### SSL Certificate Management
Certificates are automatically managed by Let's Encrypt. Manual renewal:
```bash
sudo docker compose -f docker-compose-tools-ssl.yaml exec nginx certbot renew
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
sudo docker compose -f docker-compose-tools-ssl.yaml up -d --build
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

**Tools Portal** - Professional network administration tools platform
