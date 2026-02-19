@echo off
REM setup_tunnels.bat - Windows Tunnel Wrapper for Decision Wave
echo [TUNNEL] Initializing Cloudflare Quick Tunnels...

where cloudflared >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] cloudflared.exe not found in your PATH.
    echo 1. Download it from: https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi
    echo 2. Install it, then restart this terminal.
    pause
    exit /b 1
)

echo [TUNNEL] Starting Tunnel for API (Port 8000)...
start "Cloudflare Tunnel: API" cloudflared tunnel --url http://127.0.0.1:8000

echo [TUNNEL] Starting Tunnel for Manager (Port 8001)...
start "Cloudflare Tunnel: Manager" cloudflared tunnel --url http://127.0.0.1:8001

echo [SUCCESS] Look for the 'trycloudflare.com' URLs in the two new windows!
echo [TIP] Bookmark these on your phone for easy 'Sofa Control'.
pause
