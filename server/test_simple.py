#!/usr/bin/env python3
"""
Simple setup test for Gmail integration
"""

import os
import sys
from pathlib import Path

def test_setup():
    print("Testing Gmail Integration Setup")
    print("=" * 50)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check environment variables
    print("\nEnvironment Variables:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"[OK] GEMINI_API_KEY: {'*' * 20}{gemini_key[-4:]}")
    else:
        print("[ERROR] GEMINI_API_KEY: Not set")
        return False

    # Check Google credentials file
    google_secrets_file = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "../gclientsec.json.json")
    secrets_path = Path(__file__).parent / google_secrets_file

    print(f"\nGoogle Credentials File: {secrets_path}")

    if secrets_path.exists():
        print("[OK] OAuth2 credentials found")

        # Try to read and validate
        try:
            import json
            with open(secrets_path, 'r') as f:
                creds_data = json.load(f)

            if 'installed' in creds_data or 'web' in creds_data:
                print("[OK] Credentials file format is valid")
            else:
                print("[WARNING] Unusual credentials file format")

        except Exception as e:
            print(f"[ERROR] Could not read credentials file: {e}")
            return False
    else:
        print(f"[ERROR] OAuth2 credentials file not found at: {secrets_path}")
        return False

    # Test imports
    print("\nModule Dependencies:")
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        import gmail_service
        print("[OK] gmail_service module")

        import appointment_email_handler
        print("[OK] appointment_email_handler module")

        import enhanced_system_prompt
        print("[OK] enhanced_system_prompt module")

        import gmail_routes
        print("[OK] gmail_routes module")

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False

    print("\nReadiness Check:")
    print("[OK] Environment configured")
    print("[OK] OAuth2 credentials available")
    print("[OK] All modules importable")
    print("[OK] Ready to test Gmail integration!")

    print("\nNext Steps:")
    print("1. Start the enhanced server:")
    print("   python src/pipecat_server_enhanced.py")
    print("2. Test at: http://localhost:8090/gmail/health")

    return True

if __name__ == "__main__":
    try:
        success = test_setup()
        if success:
            print("\nSetup test PASSED! Application is ready.")
        else:
            print("\nSetup test FAILED. Fix issues above.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")