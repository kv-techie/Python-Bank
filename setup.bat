@echo off
REM Scala Bank - Quick Start Script for Windows
REM This script sets up and runs the entire application

setlocal enabledelayedexpansion
set "PROJECT_DIR=%cd%"

echo.
echo ====================================
echo   Scala Bank - Full Stack Setup
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 14+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Python found: 
python --version

echo [OK] Node.js found: 
node --version

echo.
echo Step 1: Setting up Python backend...
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)

echo [OK] Python backend ready!

echo.
echo Step 2: Setting up React frontend...
echo.

REM Navigate to frontend directory
cd frontend

REM Install npm dependencies
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install npm dependencies
        cd ..
        pause
        exit /b 1
    )
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env >nul
    if %errorlevel% neq 0 (
        echo [WARNING] Failed to create .env file
    ) else (
        echo [OK] .env file created
    )
)

echo [OK] React frontend ready!

cd ..

echo.
echo ====================================
echo   Setup Complete!
echo ====================================
echo.
echo To start the application:
echo.
echo TERMINAL 1 (Backend):
echo   python app.py
echo.
echo TERMINAL 2 (Frontend):
echo   cd frontend
echo   npm start
echo.
echo Then open http://localhost:3000 in your browser
echo.
echo Admin PIN: 1234
echo.
pause
