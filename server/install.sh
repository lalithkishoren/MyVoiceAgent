#!/bin/bash
# Sutherland Voice Agent Server Installation Script for macOS/Linux

echo "🚀 Sutherland Voice Agent Server Setup (macOS/Linux)"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "✅ Python found"
python3 --version

# Create virtual environment
echo
echo "🔄 Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo
echo "🔄 Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo
echo "🔄 Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo
        echo "📄 Creating .env file from .env.example..."
        cp .env.example .env
        echo "✅ .env file created"
    else
        echo "⚠️  No .env.example found"
    fi
else
    echo "✅ .env file already exists"
fi

echo
echo "🎉 Setup completed successfully!"
echo
echo "Next steps:"
echo "1. Update your .env file with the Gemini API key"
echo "2. Run: python src/main.py"
echo "3. Server will be available at ws://localhost:8080/ws"
echo