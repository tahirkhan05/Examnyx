# OMR Blockchain Backend - Quick Setup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " OMR Blockchain Backend Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

if (-not $pythonVersion -match "Python 3\.[9-9]|Python 3\.1[0-9]") {
    Write-Host "ERROR: Python 3.9 or higher is required!" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, skipping..." -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "Virtual environment created!" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
Write-Host "Virtual environment activated!" -ForegroundColor Green

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "Dependencies installed!" -ForegroundColor Green

# Create .env file if it doesn't exist
Write-Host "`nSetting up environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host ".env file already exists, skipping..." -ForegroundColor Green
} else {
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created from template!" -ForegroundColor Green
    Write-Host "Please edit .env file with your configuration" -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "`nCreating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "audit_logs" | Out-Null
New-Item -ItemType Directory -Force -Path "temp_storage" | Out-Null
Write-Host "Directories created!" -ForegroundColor Green

# Test database initialization
Write-Host "`nInitializing database..." -ForegroundColor Yellow
python -c "from app.database import init_db; init_db(); print('Database initialized!')"
Write-Host "Database ready!" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your configuration" -ForegroundColor White
Write-Host "2. Run the server: python main.py" -ForegroundColor White
Write-Host "3. Access API docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "4. Run tests: python tests/blockchain_simulator.py" -ForegroundColor White
Write-Host ""
Write-Host "To start the server now, run:" -ForegroundColor Yellow
Write-Host "  python main.py" -ForegroundColor Cyan
Write-Host ""
