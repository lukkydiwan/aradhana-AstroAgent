# start.ps1 — launch backend + frontend in parallel (Windows PowerShell)
Write-Host "Starting Aradhana AstroAgent..." -ForegroundColor Cyan

$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\backend"
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
        .\.venv\Scripts\pip install -r requirements.txt
    }
    .\.venv\Scripts\uvicorn app.main:app --reload --port 8000
}

$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\frontend"
    if (-not (Test-Path "node_modules")) { npm install }
    npm run dev
}

Write-Host "Backend : http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow

try {
    Wait-Job $backendJob, $frontendJob
} finally {
    Stop-Job $backendJob, $frontendJob
    Remove-Job $backendJob, $frontendJob
}
