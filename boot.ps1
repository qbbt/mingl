# Master Orchestrator: MINGL-1 Boot Script

$ErrorActionPreference = "Continue"

Write-Host "Initializing MINGL-1 Platform..."

# 1. Cleanup stale processes
Write-Host "Cleaning up stale Python processes..."
taskkill /F /IM python.exe 2>$null

# 2. Wait for locks to release
Write-Host "Waiting for DuckDB-SQLite locks to clear..."
Start-Sleep -Seconds 2

# 3. Start Backend in background
Write-Host "Starting Backend (FastAPI) on Port 8000..."
$backendProcess = Start-Process python -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory "backend" -PassThru -NoNewWindow
Write-Host "   -> PID: $($backendProcess.Id)"

# 4. Wait for Backend to be ready
Write-Host "Verifying Backend Health..."
$maxRetries = 10
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 2
        if ($health.status -eq "online") {
            Write-Host "   Backend is ONLINE."
            break
        }
    } catch {
        Write-Host "   ... waiting for health check ($($retryCount + 1)/$maxRetries)"
        Start-Sleep -Seconds 2
        $retryCount++
    }
}

if ($retryCount -eq $maxRetries) {
    Write-Host "Backend failed to start."
    exit 1
}

# 5. Start Dashboard
Write-Host "Starting Dashboard (Streamlit) on Port 8001..."
$dashboardProcess = Start-Process python -ArgumentList "-m streamlit run dashboard.py --server.port 8001 --server.address 127.0.0.1 --server.headless true" -PassThru -NoNewWindow
Write-Host "   -> PID: $($dashboardProcess.Id)"

# 6. Start Autonomous Heartbeat
Write-Host "Starting Autonomous Heartbeat (Recall Loop)..."
$heartbeatProcess = Start-Process python -ArgumentList "backend/scripts/recall_loop.py" -PassThru -NoNewWindow
Write-Host "   -> PID: $($heartbeatProcess.Id)"

Write-Host "MINGL-1 is now active."
Write-Host "   Backend: http://127.0.0.1:8000"
Write-Host "   Dashboard: http://127.0.0.1:8001"
Write-Host "Press Ctrl+C to stop. Stale processes killed on next run."
