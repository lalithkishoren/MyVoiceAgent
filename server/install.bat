@echo off
REM Sutherland Voice Agent Server Installation Script for Windows

echo 🚀 Sutherland Voice Agent Server Setup (Windows)
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Create virtual environment
echo.
echo 🔄 Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo ✅ Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo 🔄 Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo 🔄 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo.
        echo 📄 Creating .env file from .env.example...
        copy .env.example .env
        echo ✅ .env file created
    ) else (
        echo ⚠️  No .env.example found
    )
) else (
    echo ✅ .env file already exists
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Update your .env file with the Gemini API key
echo 2. Run: python src/main.py
echo 3. Server will be available at ws://localhost:8080/ws
echo.
pause