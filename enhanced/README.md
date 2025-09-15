# Enhanced AI Integration Files

This directory contains enhanced versions of the Tools Portal files that include AI integration with the Symposium backend.

## Files

- `app_enhanced.py` - Enhanced Flask application with AI chat endpoints
- `config_enhanced.py` - Enhanced configuration with AI integration settings  
- `requirements_enhanced.txt` - Enhanced dependencies including AI libraries
- `index_enhanced.html` - Enhanced template with AI chat widget

## Usage

To enable AI integration, copy the enhanced files to their respective locations:

```bash
# Install enhanced dependencies
pip install -r enhanced/requirements_enhanced.txt

# Use enhanced components
cp enhanced/app_enhanced.py app.py
cp enhanced/index_enhanced.html templates/index.html
cp enhanced/config_enhanced.py config.py
```

## Documentation

See the following guides for detailed setup:
- [DEMO_AND_TESTING.md](../DEMO_AND_TESTING.md)
- [DEPLOYMENT_WITH_AI.md](../DEPLOYMENT_WITH_AI.md)

## Integration

The enhanced files provide:
- AI chat functionality through Symposium backend
- Sage interaction capabilities
- File upload for AI analysis
- Enhanced health monitoring with AI status