# Optional Submodules Guide

This document explains how to add optional submodules to the Tools Portal that are not included by default but can be added when needed.

## Overview

Some tools may be specialized or have specific licensing requirements that make them unsuitable for inclusion in the main tools repository. These can be set up as optional submodules that users can add when needed.

## Adding Optional Submodules

### Example: DND Character Generator

The DND Character Generator is an example of an optional tool that can be added as a submodule when needed.

#### Step 1: Add the Submodule

```bash
cd tools-portal
git submodule add https://gitlab.henrynet.ca/jhenry/dandd.git tools/dnd-character-generator
```

#### Step 2: Initialize the Submodule

```bash
git submodule update --init --recursive tools/dnd-character-generator
```

#### Step 3: Regenerate Configuration

```bash
python generate-compose.py
```

This will automatically detect the new tool and add it to the docker-compose configuration.

#### Step 4: Deploy with the New Tool

```bash
# Standard deployment
docker-compose -f docker-compose-tools.yaml up --build

# SSL deployment  
docker-compose -f docker-compose-tools-ssl.yaml up --build
```

## Removing Optional Submodules

### Step 1: Remove the Submodule

```bash
# Remove from .gitmodules
git config --remove-section submodule.tools/dnd-character-generator

# Remove from .git/config
git config --remove-section submodule.tools/dnd-character-generator

# Remove the directory
rm -rf tools/dnd-character-generator

# Remove from git index
git rm --cached tools/dnd-character-generator
```

### Step 2: Regenerate Configuration

```bash
python generate-compose.py
```

### Step 3: Redeploy

```bash
docker-compose -f docker-compose-tools.yaml up --build
```

## Available Optional Submodules

### DND Character Generator
- **Repository**: https://gitlab.henrynet.ca/jhenry/dandd.git
- **Description**: Comprehensive D&D 5e character creator with races, classes, backgrounds, and ability score generation
- **Category**: Gaming & Entertainment
- **Requirements**: None (self-contained)

## Best Practices for Optional Submodules

1. **Documentation**: Always document why a tool is optional
2. **Self-contained**: Optional tools should not have dependencies on other tools
3. **Clear instructions**: Provide clear add/remove instructions
4. **Testing**: Test the system both with and without the optional tool
5. **Licensing**: Ensure optional tools have compatible licensing

## Troubleshooting

### Submodule Not Detected
- Ensure the submodule has a `Dockerfile` in its root directory
- Run `python generate-compose.py` to regenerate configuration
- Check that the submodule was properly initialized

### Build Failures
- Verify the submodule repository is accessible
- Check that all dependencies are properly configured in the tool's Dockerfile
- Ensure the tool follows the standard port 5000 convention

### Deployment Issues
- Regenerate docker-compose files after adding/removing submodules
- Restart the entire stack to ensure proper routing configuration
- Check nginx configuration includes the new tool routes

## Support

For questions about optional submodules:
1. Review this guide
2. Check the tool's individual documentation
3. Verify submodule initialization
4. Test individual tool deployment before full integration

---

**Tools Portal Optional Submodules** - Flexible tool integration for specialized needs