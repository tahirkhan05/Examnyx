# ExamNyx - Start All Services
# This script starts both the backend and frontend servers

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ExamNyx - Starting All Services" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js detected: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
Write-Host ""

# Start Backend in new window
Write-Host "[1/2] Starting Blockchain Backend..." -ForegroundColor Yellow
$backendPath = "c:\Users\mdkta\OneDrive\Desktop\datanyx\project\blockchain_part"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$backendPath' ; `
     Write-Host '============================================' -ForegroundColor Cyan ; `
     Write-Host '  Blockchain Backend Server' -ForegroundColor Cyan ; `
     Write-Host '============================================' -ForegroundColor Cyan ; `
     Write-Host '' ; `
     Write-Host 'Starting server on http://localhost:8000' -ForegroundColor Green ; `
     Write-Host 'API Docs: http://localhost:8000/docs' -ForegroundColor Green ; `
     Write-Host 'Press Ctrl+C to stop' -ForegroundColor Yellow ; `
     Write-Host '' ; `
     python main.py"
)

Start-Sleep -Seconds 3

# Start Frontend in new window  
Write-Host "[2/2] Starting Frontend Server..." -ForegroundColor Yellow
$frontendPath = "c:\Users\mdkta\OneDrive\Desktop\datanyx\project\frontend"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$frontendPath' ; `
     Write-Host '============================================' -ForegroundColor Cyan ; `
     Write-Host '  Frontend Development Server' -ForegroundColor Cyan ; `
     Write-Host '============================================' -ForegroundColor Cyan ; `
     Write-Host '' ; `
     Write-Host 'Starting server on http://localhost:8080' -ForegroundColor Green ; `
     Write-Host 'Press Ctrl+C to stop' -ForegroundColor Yellow ; `
     Write-Host '' ; `
     npm run dev"
)

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Services Starting..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Frontend: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test if services are running
Write-Host ""
Write-Host "Testing services..." -ForegroundColor Yellow

try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "⚠ Backend may still be starting..." -ForegroundColor Yellow
}

try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:8080" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Frontend is running" -ForegroundColor Green
} catch {
    Write-Host "⚠ Frontend may still be starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Ready for Development!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open your browser and navigate to:" -ForegroundColor White
Write-Host "  → http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop all services, close the terminal windows." -ForegroundColor Gray
Write-Host ""
