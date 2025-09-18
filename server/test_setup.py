#!/usr/bin/env python3
"""
Quick setup test for Gmail integration
"""

import os
import sys
from pathlib import Path

def test_setup():
    print("Testing Gmail Integration Setup")
    print("=" * 50)

    # Check environment variables
    print("\nEnvironment Variables:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"[OK] GEMINI_API_KEY: {'*' * 20}{gemini_key[-4:]}")
    else:
        print("[ERROR] GEMINI_API_KEY: Not set")
        return False

    # Check Google credentials file path
    google_secrets_file = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "../gclientsec.json.json")
    secrets_path = Path(google_secrets_file)

    if not secrets_path.is_absolute():
        # Make it relative to current directory
        secrets_path = Path(__file__).parent / secrets_path

    print(f"📁 Google Credentials File: {secrets_path}")

    if secrets_path.exists():
        print(f"✅ OAuth2 credentials found")

        # Try to read and validate the JSON structure
        try:
            import json
            with open(secrets_path, 'r') as f:
                creds_data = json.load(f)

            if 'installed' in creds_data or 'web' in creds_data:
                print("✅ Credentials file format is valid")
            else:
                print("⚠️  Unusual credentials file format - may still work")

        except json.JSONDecodeError:
            print("❌ Invalid JSON in credentials file")
            return False
        except Exception as e:
            print(f"⚠️  Could not validate credentials file: {e}")

    else:
        print(f"❌ OAuth2 credentials file not found")
        print(f"   Expected at: {secrets_path}")
        return False

    # Check if we can import our modules
    print(f"\n📦 Module Dependencies:")
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        # Test imports
        import gmail_service
        print("✅ gmail_service module")

        import appointment_email_handler
        print("✅ appointment_email_handler module")

        import enhanced_system_prompt
        print("✅ enhanced_system_prompt module")

        import gmail_routes
        print("✅ gmail_routes module")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 You may need to install dependencies:")
        print("   pip install -r requirements.txt")
        return False

    print(f"\n🚀 Application Readiness:")
    print("✅ Environment configured")
    print("✅ OAuth2 credentials available")
    print("✅ All modules importable")
    print("✅ Ready to test Gmail integration!")

    print(f"\n🎯 Next Steps:")
    print("1. Start the enhanced server:")
    print("   python src/pipecat_server_enhanced.py")
    print("2. Test appointment booking with email confirmation")
    print("3. Check Gmail health endpoint:")
    print("   http://localhost:8090/gmail/health")

    return True

if __name__ == "__main__":
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()

        success = test_setup()

        if success:
            print("\n🌟 Setup test passed! Your application is ready to run.")
        else:
            print("\n⚠️  Setup test failed. Please fix the issues above.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")