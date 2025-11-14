# Tools Portal v2

**Simplified, plugin-based platform for hosting network administration and system tools.**

## What Changed in v2?

### ✨ Major Improvements

| Feature | v1 | v2 |
|---------|----|----|
| **Configuration** | 7+ files, 979 lines | 3 files, ~100 lines |
| **Tool Integration** | Git submodules + generation scripts | Drop-in plugins |
| **Deployment** | 5+ manual steps | `docker compose up` |
| **SSL Setup** | Manual nginx config | Automatic (Caddy) |
| **Architecture** | Mixed approach | Clean plugin system |

### 🎯 Key Features

- **Drop-in Plugin Architecture**: Add tools by copying directories
- **Auto-SSL with Caddy**: Automatic Let's Encrypt certificates
- **Simplified Deployment**: Single `docker-compose.yml`
- **Clean Code Structure**: Modular Flask application
- **Auto-Discovery**: Tools automatically registered at startup

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Domain name for HTTPS

### 1. Clone Repository

```bash
git clone https://github.com/apathy-ca/tools-portal.git
cd tools-portal
git checkout claude/code-review-feedback-011CUhQJUEbpq6AQCc9B6eUj  # v2 branch
```

### 2. Deploy

**Development (HTTP only):**
```bash
docker compose up -d
```

Access at: `http://localhost/`

**Production (HTTPS with auto-SSL):**
```bash
# Edit Caddyfile - replace 'your-domain.com' with your actual domain
nano Caddyfile

# Deploy
docker compose up -d
```

Access at: `https://your-domain.com/`

That's it! Caddy handles SSL certificates automatically.

---

## Architecture

### Directory Structure

```
tools-portal-v2/
├── app/                    # Main application
│   ├── __init__.py        # Flask factory
│   ├── config.py          # Configuration
│   ├── core/              # Core routes
│   │   └── routes.py      # Dashboard, API, health
│   ├── tools/             # Tool plugins (auto-discovered)
│   │   ├── dns_by_eye/    # DNS delegation tool
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   └── ipwhale/       # IP information tool
│   │       ├── __init__.py
│   │       └── routes.py
│   └── templates/         # HTML templates
│       ├── index.html
│       ├── 404.html
│       └── 500.html
│
├── tools/                 # Original tool repositories (legacy)
│   ├── dns-by-eye/
│   └── ipwhale/
│
├── docker-compose.yml     # Single deployment file
├── Caddyfile              # Auto-SSL configuration
├── Dockerfile             # Application container
├── requirements.txt       # Python dependencies
├── run.py                 # Application entry point
└── README.v2.md           # This file
```

### How It Works

1. **Flask Factory** (`app/__init__.py`): Creates app instance
2. **Plugin Discovery** (`app/tools/__init__.py`): Scans `app/tools/` directory
3. **Blueprint Registration**: Each tool registers routes automatically
4. **Caddy Proxy**: Handles SSL and proxies to Flask app

---

## Adding New Tools

### Option 1: Create New Plugin

```bash
# Create tool directory
mkdir -p app/tools/my_tool

# Create __init__.py
cat > app/tools/my_tool/__init__.py << 'EOF'
from flask import Blueprint

blueprint = Blueprint('my_tool', __name__)

TOOL_INFO = {
    'name': 'My Tool',
    'description': 'Does something useful',
    'version': '1.0.0',
    'icon': '🔧',
    'category': 'Utilities',
    'status': 'stable',
    'features': ['Feature 1', 'Feature 2'],
    'tags': ['utility', 'tool']
}

from . import routes
EOF

# Create routes.py
cat > app/tools/my_tool/routes.py << 'EOF'
from flask import jsonify
from . import blueprint

@blueprint.route('/')
def index():
    return "Hello from My Tool!"

@blueprint.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})
EOF

# Restart
docker compose restart tools-portal
```

Your tool is now available at `/my_tool/`!

### Option 2: Copy Existing Tool

```bash
# Copy tool directory
cp -r ~/path/to/existing/tool app/tools/

# Edit __init__.py to add TOOL_INFO and blueprint
# Restart
docker compose restart tools-portal
```

---

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Security
SECRET_KEY=your-secret-key-here

# Logging
LOG_LEVEL=INFO

# Cache (optional)
CACHE_TYPE=simple
# REDIS_URL=redis://redis:6379/0

# Database (optional - for future features)
# DATABASE_URL=postgresql://user:pass@postgres:5432/tools_portal
```

### Caddy Configuration

Edit `Caddyfile` for production:

```caddy
# Replace with your domain
your-domain.com {
    reverse_proxy tools-portal:5000
    encode gzip
    log {
        output stdout
        format json
    }
}
```

Caddy automatically:
- Gets Let's Encrypt certificates
- Renews certificates
- Redirects HTTP → HTTPS

---

## API Endpoints

### Core Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main dashboard |
| `GET /api/tools` | List all tools (JSON) |
| `GET /health` | Basic health check |
| `GET /api/health/detailed` | Detailed health + metrics |

### Tool Endpoints

Each tool is available at `/{tool_name}/`:

- **DNS By Eye**: `/dns_by_eye/`
  - `/dns_by_eye/api/health`
  - `/dns_by_eye/api/trace/<domain>`
  - `/dns_by_eye/api/delegation`

- **IP Whale**: `/ipwhale/`
  - `/ipwhale/api/health`
  - `/ipwhale/api/ip`
  - `/ipwhale/api/full`
  - `/ipwhale/api/4/ip` (curl-friendly)
  - `/ipwhale/api/6/ip` (curl-friendly)

---

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (without Docker)
python run.py

# Access at http://localhost:5000
```

### Hot Reload

For development with hot reload:

```yaml
# Add to docker-compose.yml tools-portal service:
volumes:
  - ./app:/app/app
  - ./tools:/app/tools:ro
environment:
  - DEBUG=true
```

### Testing

```bash
# Test health endpoint
curl http://localhost/health

# Test API
curl http://localhost/api/tools

# Test tool
curl http://localhost/dns_by_eye/api/health
```

---

## Monitoring & Health Checks

### Health Endpoints

```bash
# Basic health
curl http://localhost/health

# Detailed health with metrics
curl http://localhost/api/health/detailed
```

### Logs

```bash
# View all logs
docker compose logs -f

# View portal logs only
docker compose logs -f tools-portal

# View Caddy logs
docker compose logs -f caddy
```

### Metrics

Detailed health endpoint returns:
- Service status
- Registered tools
- CPU usage
- Memory usage
- Disk usage

---

## Migration from v1

### What to Keep

- Tool code in `tools/` directory (legacy)
- SSL certificates (if using)
- Custom configurations

### What to Delete

```bash
# Old v1 files (after migrating)
rm -f generate-compose.py
rm -f dynamic_tools.py
rm -f nginx-tools.conf nginx-tools-ssl.conf
rm -f docker-compose-tools.yaml docker-compose-tools-ssl.yaml
rm -f gunicorn_config.py
rm -f config.py  # (v1 version)
```

### Migration Steps

1. Backup your v1 installation
2. Clone v2 branch
3. Copy tool code to `app/tools/` as plugins
4. Update `Caddyfile` with your domain
5. Deploy: `docker compose up -d`
6. Test all tools
7. Update DNS if needed

---

## Troubleshooting

### Tools Not Appearing

```bash
# Check logs
docker compose logs tools-portal

# Verify plugin structure
ls -la app/tools/your_tool/

# Ensure __init__.py has TOOL_INFO and blueprint
cat app/tools/your_tool/__init__.py
```

### SSL Issues

```bash
# Check Caddy logs
docker compose logs caddy

# Verify domain in Caddyfile
grep "your-domain" Caddyfile

# Ensure ports 80 and 443 are open
netstat -tulpn | grep -E ':(80|443)'
```

### Tool Import Errors

```bash
# Check Python path issues
docker compose exec tools-portal python -c "import sys; print(sys.path)"

# Test tool import
docker compose exec tools-portal python -c "from app.tools.dns_by_eye import TOOL_INFO; print(TOOL_INFO)"
```

---

## Comparison: v1 vs v2

### Deployment

**v1:**
```bash
git clone --recursive https://github.com/apathy-ca/tools-portal.git
git submodule update --init --recursive
python generate-compose.py
sed -i 's/your-domain.com/actual-domain.com/g' nginx-tools-ssl.conf
./scripts/setup-ssl.sh domain.com email
docker compose -f docker-compose-tools-ssl.yaml up -d
```

**v2:**
```bash
git clone https://github.com/apathy-ca/tools-portal.git
cd tools-portal
# Edit Caddyfile with your domain
docker compose up -d
```

### Adding Tools

**v1:**
```bash
git submodule add https://github.com/user/tool.git tools/tool
python generate-compose.py
docker compose -f docker-compose-tools.yaml up --build
```

**v2:**
```bash
cp -r ~/tool app/tools/
docker compose restart tools-portal
```

### Configuration Changes

**v1:** Regenerate config files
```bash
python generate-compose.py
docker compose restart
```

**v2:** Edit and restart
```bash
nano Caddyfile  # or docker-compose.yml
docker compose restart
```

---

## Future Enhancements

### Planned for v2.1

- [ ] Web-based admin panel
- [ ] Tool enable/disable without restart
- [ ] Built-in metrics dashboard
- [ ] User authentication (optional)
- [ ] API keys for rate limiting
- [ ] Database integration (PostgreSQL)

### Contributions Welcome

- New tool plugins
- UI improvements
- Documentation
- Bug fixes

---

## License

MIT License - see LICENSE file

## Credits

Built with:
- **Flask** - Web framework
- **Caddy** - Web server with auto-SSL
- **Docker** - Containerization
- **Python** - Core language

Created with assistance from ChatGPT and Claude (Anthropic).

---

## Support

- **Issues**: [GitHub Issues](https://github.com/apathy-ca/tools-portal/issues)
- **Docs**: This README
- **Community**: GitHub Discussions

---

**Tools Portal v2** - Making tool deployment simple again.
