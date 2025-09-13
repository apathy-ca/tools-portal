# IPWhale Enablement Script for Tools-Portal (Windows PowerShell)
# This script enables IPWhale in an already-built tools-portal system

param(
    [switch]$Force = $false
)

Write-Host "🐋 IPWhale Enablement Script (Windows)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if we're in the tools-portal directory
if (-not (Test-Path "docker compose-tools.yaml")) {
    Write-Host "❌ Error: Please run this script from the tools-portal directory" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Checking current setup..." -ForegroundColor Yellow

# Check if IPWhale submodule exists
if (-not (Test-Path "tools\ipwhale")) {
    Write-Host "⚠️  IPWhale submodule not found. Setting up..." -ForegroundColor Yellow
    
    # Add IPWhale as submodule
    git submodule add https://github.com/apathy-ca/ipwhale.git tools/ipwhale
    git submodule init
    git submodule update --recursive --remote
    
    Write-Host "✅ IPWhale submodule added successfully" -ForegroundColor Green
} else {
    Write-Host "✅ IPWhale submodule already exists" -ForegroundColor Green
    
    # Update submodule to latest
    Write-Host "🔄 Updating IPWhale to latest version..." -ForegroundColor Yellow
    git submodule update --remote tools/ipwhale
}

# Check if IPWhale is configured in app.py
if (Select-String -Path "app.py" -Pattern "ipwhale" -Quiet) {
    Write-Host "✅ IPWhale already configured in app.py" -ForegroundColor Green
} else {
    Write-Host "⚠️  IPWhale not found in app.py configuration" -ForegroundColor Yellow
    Write-Host "   Please ensure IPWhale is added to the TOOLS registry in app.py" -ForegroundColor Yellow
}

# Check if IPWhale is in docker compose
if (Select-String -Path "docker compose-tools.yaml" -Pattern "ipwhale:" -Quiet) {
    Write-Host "✅ IPWhale already configured in docker compose-tools.yaml" -ForegroundColor Green
} else {
    Write-Host "⚠️  IPWhale not found in docker compose-tools.yaml" -ForegroundColor Yellow
    Write-Host "   Please ensure IPWhale service is defined in docker compose-tools.yaml" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Starting IPWhale deployment..." -ForegroundColor Cyan

# Build and start IPWhale
Write-Host "🔨 Building IPWhale container..." -ForegroundColor Yellow
docker compose -f docker compose-tools.yaml build ipwhale

Write-Host "🏃 Starting IPWhale service..." -ForegroundColor Yellow
docker compose -f docker compose-tools.yaml up -d ipwhale

# Wait a moment for startup
Write-Host "⏳ Waiting for IPWhale to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test IPWhale health
Write-Host "🏥 Testing IPWhale health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/ipwhale/api/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ IPWhale is healthy and responding" -ForegroundColor Green
    } else {
        Write-Host "⚠️  IPWhale health check returned status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  IPWhale health check failed - checking container logs..." -ForegroundColor Yellow
    docker logs ipwhale --tail 20
}

Write-Host ""
Write-Host "🎉 IPWhale Enablement Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   Web Interface: http://localhost/ipwhale/" -ForegroundColor White
Write-Host "   API Health:    http://localhost/ipwhale/api/health" -ForegroundColor White
Write-Host "   IPv4 API:      http://localhost/ipwhale/api/4/ip" -ForegroundColor White
Write-Host "   Full API:      http://localhost/ipwhale/api/full" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Management Commands:" -ForegroundColor Cyan
Write-Host "   View logs:     docker logs ipwhale" -ForegroundColor White
Write-Host "   Restart:       docker compose -f docker compose-tools.yaml restart ipwhale" -ForegroundColor White
Write-Host "   Update:        git submodule update --remote tools/ipwhale; docker compose -f docker compose-tools.yaml up --build ipwhale" -ForegroundColor White
Write-Host ""
Write-Host "📚 For more information, see IPWHALE_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan

# Test some API endpoints
Write-Host ""
Write-Host "🧪 Quick API Tests:" -ForegroundColor Cyan
try {
    $ip = Invoke-RestMethod -Uri "http://localhost/ipwhale/api/ip" -TimeoutSec 5
    Write-Host "   Your IP: $ip" -ForegroundColor White
} catch {
    Write-Host "   IP API test failed" -ForegroundColor Yellow
}

try {
    $health = Invoke-RestMethod -Uri "http://localhost/ipwhale/api/health" -TimeoutSec 5
    Write-Host "   Health Status: $($health.status)" -ForegroundColor White
} catch {
    Write-Host "   Health API test failed" -ForegroundColor Yellow
}
