# CI Pipeline Local Test Script
# This script simulates the GitHub Actions CI pipeline locally

Write-Host ""
Write-Host "Starting CI Pipeline Local Test..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Start PostgreSQL service
Write-Host "Step 1: Starting PostgreSQL service..." -ForegroundColor Yellow
docker-compose up -d db

# Wait for PostgreSQL to be ready
Write-Host "Step 2: Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$maxRetries = 30
$retryCount = 0
$isReady = $false

while (-not $isReady -and $retryCount -lt $maxRetries) {
    $retryCount++
    Start-Sleep -Seconds 1
    
    # Check if PostgreSQL is accepting connections
    $result = docker-compose exec -T db pg_isready -U cv_filter -d cv_filter 2>&1
    if ($result -match "accepting connections") {
        $isReady = $true
        Write-Host "PostgreSQL is ready!" -ForegroundColor Green
    } else {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $isReady) {
    Write-Host ""
    Write-Host "PostgreSQL failed to start!" -ForegroundColor Red
    docker-compose down
    exit 1
}
Write-Host ""

# Step 3: Set up environment variables (same as CI)
Write-Host "Step 3: Setting up environment variables..." -ForegroundColor Yellow
$env:DJANGO_SECRET_KEY = "test-secret-key-for-ci-only-do-not-use-in-production"
$env:DJANGO_DEBUG = "True"
$env:DJANGO_ALLOWED_HOSTS = "*"
$env:POSTGRES_DB = "cv_filter"
$env:POSTGRES_USER = "cv_filter"
$env:POSTGRES_PASSWORD = "cv_filter"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"

# Step 4: Check if virtual environment exists
Write-Host "Step 4: Setting up Python environment..." -ForegroundColor Yellow
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv .venv
}

# Step 5: Install dependencies
Write-Host "Step 5: Installing dependencies..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.\.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet

# Step 6: Run migrations
Write-Host "Step 6: Running database migrations..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe apps/api/cv_filter/manage.py migrate --noinput

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Migration failed!" -ForegroundColor Red
    docker-compose down
    exit 1
}

# Step 7: Run tests
Write-Host "Step 7: Running tests..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe apps/api/cv_filter/manage.py test ranking.tests -v 2

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Tests failed!" -ForegroundColor Red
    docker-compose down
    exit 1
}

# Success!
Write-Host ""
Write-Host "All tests passed!" -ForegroundColor Green

# Step 8: Cleanup
Write-Host "Step 8: Cleaning up..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "CI Pipeline test completed successfully!" -ForegroundColor Cyan
Write-Host ""
