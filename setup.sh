#!/bin/bash

# HaikuBot Setup Script

set -e

echo "🤖 HaikuBot Setup"
echo "=================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo ""
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create config if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo ""
    echo "Creating config.yaml from example..."
    cp config.yaml.example config.yaml
    echo "⚠️  Please edit config.yaml with your IRC server details!"
else
    echo ""
    echo "config.yaml already exists"
fi

# Setup frontend
echo ""
echo "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
else
    echo "Node.js dependencies already installed"
fi

# Build frontend for production
echo ""
read -p "Build frontend for production? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Building frontend..."
    npm run build
    echo "✅ Frontend built to frontend/dist/"
fi

cd ..

# Done
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your IRC server settings"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python -m backend.main"
echo ""
echo "For development:"
echo "- Backend: python -m backend.main"
echo "- Frontend: cd frontend && npm run dev"
echo ""
echo "Documentation:"
echo "- README.md - Setup and usage guide"
echo "- PROJECT_PLAN.md - Detailed project plan"
echo "- CLAUDE.md - AI assistant context"
echo ""

