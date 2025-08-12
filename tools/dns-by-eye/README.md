# DNS By Eye

**Version 1.0.2**

DNS By Eye is a Flask-based DNS delegation visualizer. It traces DNS delegation chains from the root through TLDs to the authoritative nameservers, then renders interactive graphs of each layer and cross-reference diagrams.

## Features

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

## Standalone Usage

If you want to run DNS By Eye as a standalone application:

```bash
cd tools/dns-by-eye
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app/main.py
```

Open http://localhost:5000 in your browser.

## Docker (Standalone)

```bash
cd tools/dns-by-eye
docker build -t dns-by-eye .
docker run --rm -p 5000:5000 dns-by-eye
```

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

### Simple Trace
```http
GET /api/trace/example.com?verbose=true&dns_server=8.8.8.8
```

### Export Data
```http
GET /api/export/example.com?format=json&verbose=true
```

## Test Domain

Try the intentionally broken `test.apathy.ca` domain to see DNS By Eye's error handling capabilities.

## License

This project is licensed under the MIT License.
