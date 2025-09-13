@echo off
setlocal enabledelayedexpansion

echo 🚀 Tools Portal Deployment Script
echo =================================

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: Please run from tools-portal directory
    exit /b 1
)

REM Initialize submodules if they exist
if exist ".gitmodules" (
    echo 📦 Initializing git submodules...
    git submodule update --init --recursive
    if !errorlevel! neq 0 (
        echo ❌ Failed to initialize submodules
        exit /b 1
    )
    echo ✅ Submodules initialized
) else (
    echo ℹ️  No submodules found
)

REM Verify tools are available
echo 🔍 Verifying tools...
set tool_count=0
for /d %%i in (tools\*) do (
    if exist "%%i\Dockerfile" (
        echo ✅ Found: %%~ni ^(with Dockerfile^)
        set /a tool_count+=1
    ) else (
        if exist "%%i" (
            echo ⚠️  Warning: %%~ni missing Dockerfile - will be skipped
        )
    )
)

if !tool_count! equ 0 (
    echo ❌ No tools with Dockerfiles found!
    echo 💡 Make sure submodules are properly initialized
    exit /b 1
)

REM Generate compose files
echo 🐋 Generating Docker Compose configuration...

REM Try different Python commands
python generate-compose.py 2>nul
if !errorlevel! equ 0 (
    echo ✅ Docker Compose files generated successfully
    goto :deploy_success
)

python3 generate-compose.py 2>nul
if !errorlevel! equ 0 (
    echo ✅ Docker Compose files generated successfully
    goto :deploy_success
)

py generate-compose.py 2>nul
if !errorlevel! equ 0 (
    echo ✅ Docker Compose files generated successfully
    goto :deploy_success
)

echo ❌ Failed to generate Docker Compose files
echo 💡 Python not found. Please install Python or ensure it's in your PATH
echo    Try: python, python3, or py
exit /b 1

:deploy_success

echo.
echo 🎉 Deployment preparation complete!
echo.
echo 📋 Next steps:
echo    For development: docker compose -f docker compose-tools.yaml up --build
echo    For production:  docker compose -f docker compose-tools-ssl.yaml up --build
echo.
echo ⚠️  For SSL deployment, make sure to:
echo    1. Update nginx-tools-ssl.conf with your domain
echo    2. Run scripts\setup-ssl.sh your-domain.com your-email@domain.com
echo.