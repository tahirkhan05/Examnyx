# Backend and Frontend Integration Test Script

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "ExamNyx - Integration Verification" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check if backend is running
Write-Host "[1/5] Testing Backend Server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    $healthData = $response.Content | ConvertFrom-Json
    if ($healthData.status -eq "healthy") {
        Write-Host "  SUCCESS Backend is healthy" -ForegroundColor Green
        if ($healthData.blockchain) {
            Write-Host "  - Blockchain valid: $($healthData.blockchain.is_valid)" -ForegroundColor Gray
            Write-Host "  - Total blocks: $($healthData.blockchain.total_blocks)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  WARNING Backend is unhealthy" -ForegroundColor Red
    }
}
catch {
    Write-Host "  ERROR Backend not responding at http://localhost:8000" -ForegroundColor Red
    Write-Host "  Please start the backend server first!" -ForegroundColor Yellow
}

Write-Host ""

# Test 2: Check API endpoints
Write-Host "[2/5] Testing API Endpoints..." -ForegroundColor Yellow
$endpoints = @(
    "/api/blockchain/status",
    "/api/blockchain/blocks"
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000$endpoint" -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  SUCCESS $endpoint" -ForegroundColor Green
    }
    catch {
        Write-Host "  FAILED $endpoint" -ForegroundColor Red
    }
}

Write-Host ""

# Test 3: Check frontend files
Write-Host "[3/5] Checking Frontend Configuration..." -ForegroundColor Yellow
$frontendPath = "c:\Users\mdkta\OneDrive\Desktop\datanyx\project\frontend"

if (Test-Path "$frontendPath\.env") {
    Write-Host "  SUCCESS .env file exists" -ForegroundColor Green
    $envContent = Get-Content "$frontendPath\.env"
    $apiUrl = $envContent | Where-Object { $_ -match "VITE_API_BASE_URL" }
    Write-Host "    $apiUrl" -ForegroundColor Gray
}
else {
    Write-Host "  ERROR .env file missing" -ForegroundColor Red
}

if (Test-Path "$frontendPath\src\lib\api.ts") {
    Write-Host "  SUCCESS API configuration file exists" -ForegroundColor Green
}
else {
    Write-Host "  ERROR API configuration file missing" -ForegroundColor Red
}

if (Test-Path "$frontendPath\src\services\api.service.ts") {
    Write-Host "  SUCCESS API service file exists" -ForegroundColor Green
}
else {
    Write-Host "  ERROR API service file missing" -ForegroundColor Red
}

Write-Host ""

# Test 4: Check node_modules
Write-Host "[4/5] Checking Frontend Dependencies..." -ForegroundColor Yellow
Push-Location $frontendPath
$packageJson = Get-Content "package.json" | ConvertFrom-Json
if ($packageJson.dependencies.axios) {
    Write-Host "  SUCCESS axios dependency configured" -ForegroundColor Green
}
else {
    Write-Host "  ERROR axios dependency missing" -ForegroundColor Red
}

if (Test-Path "node_modules\axios") {
    Write-Host "  SUCCESS axios installed" -ForegroundColor Green
}
else {
    Write-Host "  WARNING axios not installed - run 'npm install'" -ForegroundColor Yellow
}
Pop-Location

Write-Host ""

# Test 5: Check if frontend is accessible
Write-Host "[5/5] Testing Frontend Server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  SUCCESS Frontend is accessible at http://localhost:8080" -ForegroundColor Green
}
catch {
    Write-Host "  INFO Frontend not running at http://localhost:8080" -ForegroundColor Yellow
    Write-Host "    Start with: cd frontend ; npm run dev" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Integration Summary" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Frontend: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "To start services:" -ForegroundColor Yellow
Write-Host "  Backend:  cd blockchain_part ; python main.py" -ForegroundColor Gray
Write-Host "  Frontend: cd frontend ; npm run dev" -ForegroundColor Gray
Write-Host ""
