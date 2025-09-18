#!/usr/bin/env python3
"""
Sutherland Voice Agent Server Setup Script
Installs all required dependencies and sets up the environment.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.8 or higher.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def main():
    """Main setup function."""
    print("🚀 Sutherland Voice Agent Server Setup")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Change to server directory
    server_dir = Path(__file__).parent
    os.chdir(server_dir)
    print(f"📁 Working directory: {server_dir}")

    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found in current directory")
        sys.exit(1)

    # Upgrade pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        print("⚠️  Failed to upgrade pip, continuing anyway...")

    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing dependencies"):
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Check if .env file exists
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("\n📄 Creating .env file from .env.example...")
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ .env file created. Please update it with your API keys.")
        else:
            print("⚠️  No .env.example found. Please create .env manually.")
    else:
        print("✅ .env file already exists")

    # Verify installation
    print("\n🔍 Verifying installation...")
    try:
        import pipecat
        import google.generativeai
        import fastapi
        import websockets
        print("✅ All core packages imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)

    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update your .env file with the Gemini API key")
    print("2. Run the server: python src/main.py")
    print("3. The server will be available at ws://localhost:8080/ws")

if __name__ == "__main__":
    main()