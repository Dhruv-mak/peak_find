# Peak Finder Pro GUI Launcher
# PowerShell script to set up and run the GUI application

Write-Host "🚀 Peak Finder Pro - GUI Launcher" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Virtual environment created." -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/upgrade requirements
Write-Host "📥 Installing GUI requirements..." -ForegroundColor Yellow
pip install -r requirements_gui.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Some packages may not have installed correctly." -ForegroundColor Yellow
}

Write-Host "✅ Dependencies installed." -ForegroundColor Green
Write-Host ""

# Run the GUI
Write-Host "🎨 Starting Peak Finder Pro GUI..." -ForegroundColor Magenta
Write-Host ""

python gui_main.py

Write-Host ""
Write-Host "👋 Thanks for using Peak Finder Pro!" -ForegroundColor Cyan
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
