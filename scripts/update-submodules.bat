@echo off
REM Update Submodules to Latest Script (Windows)
REM This script updates all submodules to their latest commits on their tracked branches

echo 🔄 Updating submodules to latest versions...

REM Update all submodules to their latest remote commits
git submodule update --remote

REM Check if there are any changes to commit
git diff --quiet --exit-code
if %errorlevel% equ 0 (
    echo ✅ All submodules are already up to date!
) else (
    echo 📝 Submodule updates detected. Committing changes...
    
    REM Add the submodule updates
    git add .
    
    REM Create a commit message with timestamp
    for /f "tokens=1-4 delims=/ " %%i in ('date /t') do set mydate=%%i-%%j-%%k
    for /f "tokens=1-2 delims=: " %%i in ('time /t') do set mytime=%%i:%%j
    
    git commit -m "Update submodules to latest versions - %mydate% %mytime%"
    
    echo ✅ Submodule updates committed!
    echo.
    echo 🚀 To push these changes, run:
    echo    git push
)

echo.
echo 📋 Current submodule status:
git submodule status

pause