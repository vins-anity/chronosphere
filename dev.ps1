<# 
.SYNOPSIS
    Chronosphere - Developer Commands (Windows)

.DESCRIPTION
    Run: .\dev.ps1 <command>
    Commands: help, install, dev, dev-backend, dev-frontend, services, 
              docker-up, docker-down, migrate, test, lint, collect, train

.EXAMPLE
    .\dev.ps1 help
    .\dev.ps1 dev
#>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Write-Header($text) {
    Write-Host "`n$text" -ForegroundColor Cyan
    Write-Host ("=" * 50) -ForegroundColor DarkGray
}

function Show-Help {
    Write-Host ""
    Write-Host "Chronosphere" -ForegroundColor Cyan -NoNewline
    Write-Host " - Developer Commands"
    Write-Host ""
    Write-Host "Usage: " -NoNewline
    Write-Host ".\dev.ps1 <command>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  help          " -ForegroundColor Cyan -NoNewline
    Write-Host "Show this help message"
    Write-Host "  install       " -ForegroundColor Cyan -NoNewline
    Write-Host "Install all dependencies (backend + frontend)"
    Write-Host "  dev           " -ForegroundColor Cyan -NoNewline
    Write-Host "Start full dev environment"
    Write-Host "  dev-backend   " -ForegroundColor Cyan -NoNewline
    Write-Host "Start backend with hot reload"
    Write-Host "  dev-frontend  " -ForegroundColor Cyan -NoNewline
    Write-Host "Start frontend dev server"
    Write-Host "  services      " -ForegroundColor Cyan -NoNewline
    Write-Host "Start DB + Redis containers"
    Write-Host "  docker-up     " -ForegroundColor Cyan -NoNewline
    Write-Host "Start full Docker stack"
    Write-Host "  docker-down   " -ForegroundColor Cyan -NoNewline
    Write-Host "Stop Docker stack"
    Write-Host "  docker-logs   " -ForegroundColor Cyan -NoNewline
    Write-Host "View Docker logs"
    Write-Host "  migrate       " -ForegroundColor Cyan -NoNewline
    Write-Host "Run database migrations"
    Write-Host "  test          " -ForegroundColor Cyan -NoNewline
    Write-Host "Run all tests"
    Write-Host "  lint          " -ForegroundColor Cyan -NoNewline
    Write-Host "Run linter"
    Write-Host "  collect       " -ForegroundColor Cyan -NoNewline
    Write-Host "Collect ML training data"
    Write-Host "  train         " -ForegroundColor Cyan -NoNewline
    Write-Host "Train ML model"
    Write-Host "  clean         " -ForegroundColor Cyan -NoNewline
    Write-Host "Clean generated files"
    Write-Host ""
}

function Install-Deps {
    Write-Header "Installing backend dependencies..."
    uv sync
    Write-Header "Installing frontend dependencies..."
    Push-Location frontend
    npm install
    Pop-Location
    Write-Host "`nDone!" -ForegroundColor Green
}

function Start-Dev {
    Write-Header "Starting development environment..."
    docker compose up -d db redis
    Write-Host "Waiting for services..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    Write-Host "Starting backend and frontend..." -ForegroundColor Green
    Write-Host "Backend: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    # Start both in parallel
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; uv run uvicorn app.ingest.main:app --reload --host 0.0.0.0 --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"
}

function Start-Backend {
    Write-Header "Starting backend..."
    uv run uvicorn app.ingest.main:app --reload --host 0.0.0.0 --port 8000
}

function Start-Frontend {
    Write-Header "Starting frontend..."
    Push-Location frontend
    npm run dev
    Pop-Location
}

function Start-Services {
    Write-Header "Starting database and cache services..."
    docker compose up -d db redis
    Write-Host "`nServices started!" -ForegroundColor Green
    Write-Host "  PostgreSQL: localhost:5432"
    Write-Host "  Redis:      localhost:6379"
}

function Start-DockerUp {
    Write-Header "Starting Docker stack..."
    docker compose up --build -d
}

function Start-DockerDown {
    Write-Header "Stopping Docker stack..."
    docker compose down
}

function Start-DockerLogs {
    docker compose logs -f
}

function Run-Migrate {
    Write-Header "Running migrations..."
    uv run alembic upgrade head
}

function Run-Tests {
    Write-Header "Running tests..."
    uv run pytest tests/ -v
}

function Run-Lint {
    Write-Header "Running linter..."
    uv run ruff check app/
}

function Run-Collect {
    Write-Header "Collecting training data..."
    uv run python -c "from app.ml.collect import main; import asyncio; asyncio.run(main())"
}

function Run-Train {
    Write-Header "Training model..."
    uv run python -c "from app.ml.train import train_model; train_model()"
}

function Clean-Project {
    Write-Header "Cleaning generated files..."
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Directory -Filter ".pytest_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Directory -Filter ".ruff_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }
    if (Test-Path ".coverage") { Remove-Item -Force ".coverage" }
    Write-Host "Done!" -ForegroundColor Green
}

# Command dispatcher
switch ($Command.ToLower()) {
    "help"          { Show-Help }
    "install"       { Install-Deps }
    "dev"           { Start-Dev }
    "dev-backend"   { Start-Backend }
    "dev-frontend"  { Start-Frontend }
    "services"      { Start-Services }
    "docker-up"     { Start-DockerUp }
    "docker-down"   { Start-DockerDown }
    "docker-logs"   { Start-DockerLogs }
    "migrate"       { Run-Migrate }
    "test"          { Run-Tests }
    "lint"          { Run-Lint }
    "collect"       { Run-Collect }
    "train"         { Run-Train }
    "clean"         { Clean-Project }
    default         { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help 
    }
}
