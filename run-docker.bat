@echo off
echo Starting BNB Financial Manager with Docker...
echo.

:: Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

:: Create database file with schema if it doesn't exist
if not exist "finance.db" (
    echo Creating database with schema...
    python create_empty_db.py
    if %errorlevel% neq 0 (
        echo Warning: Python not found, creating empty file instead...
        type nul > finance.db
    )
)

echo Building and starting the application...
docker-compose up --build

echo.
echo Application stopped. Press any key to exit...
pause >nul