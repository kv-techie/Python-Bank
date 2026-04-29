#!/bin/bash

# Scala Bank - Quick Start Script for macOS/Linux
# This script sets up and runs the entire application

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "===================================="
echo "  Scala Bank - Full Stack Setup"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed or not in PATH"
    echo "Please install Node.js 14+ from https://nodejs.org/"
    exit 1
fi

echo "[OK] Python found:"
python3 --version

echo "[OK] Node.js found:"
node --version

echo ""
echo "Step 1: Setting up Python backend..."
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install Python dependencies"
    exit 1
fi

echo "[OK] Python backend ready!"

echo ""
echo "Step 2: Setting up React frontend..."
echo ""

# Navigate to frontend directory
cd frontend

# Install npm dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install npm dependencies"
        cd ..
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    if [ $? -ne 0 ]; then
        echo "[WARNING] Failed to create .env file"
    else
        echo "[OK] .env file created"
    fi
fi

echo "[OK] React frontend ready!"

cd ..

echo ""
echo "===================================="
echo "   Setup Complete!"
echo "===================================="
echo ""
echo "To start the application:"
echo ""
echo "TERMINAL 1 (Backend):"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "TERMINAL 2 (Frontend):"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""
echo "Admin PIN: 1234"
echo ""
