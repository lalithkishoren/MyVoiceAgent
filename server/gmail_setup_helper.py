#!/usr/bin/env python3
"""
Gmail Setup Helper
Guides you through Gmail OAuth2 setup and tests the integration
"""

import os
import sys
import json
import subprocess
import webbrowser
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step_number, title):
    """Print a formatted step"""
    print(f"\n📋 Step {step_number}: {title}")
    print("-" * 40)

def check_file_exists(filepath, description):
    """Check if a file exists and return status"""
    if os.path.exists(filepath):
        print(f"✅ {description} found: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False

def main():
    print_header("Gmail Integration Setup Helper")
    print("This script will guide you through setting up Gmail integration for your voice agent.")

    current_dir = Path(__file__).parent
    server_dir = current_dir

    # Step 1: Check current setup
    print_step(1, "Checking Current Setup")

    # Check for required files
    client_secrets_path = server_dir / "client_secrets.json"
    token_path = server_dir / "google_token.pickle"
    env_path = server_dir / ".env"

    client_secrets_exists = check_file_exists(client_secrets_path, "OAuth2 credentials file")
    token_exists = check_file_exists(token_path, "OAuth2 token file")
    env_exists = check_file_exists(env_path, "Environment file")

    # Check environment variables
    print(f"\n🔍 Environment Variables:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"✅ GEMINI_API_KEY: {'*' * 20}{gemini_key[-4:]}")
    else:
        print(f"❌ GEMINI_API_KEY: Not set")

    google_secrets_file = os.getenv("GOOGLE_CLIENT_SECRETS_FILE")
    if google_secrets_file:
        print(f"✅ GOOGLE_CLIENT_SECRETS_FILE: {google_secrets_file}")
    else:
        print(f"⚠️  GOOGLE_CLIENT_SECRETS_FILE: Not set (will use default: client_secrets.json)")

    # Step 2: Guide through OAuth setup if needed
    if not client_secrets_exists:
        print_step(2, "OAuth2 Credentials Setup Required")
        print("You need to create OAuth2 credentials in Google Cloud Console.")
        print("\n📝 Instructions:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Select your project or create a new one")
        print("3. Enable the Gmail API:")
        print("   - Go to 'APIs & Services' → 'Library'")
        print("   - Search for 'Gmail API' and click 'Enable'")
        print("4. Create OAuth2 Credentials:")
        print("   - Go to 'APIs & Services' → 'Credentials'")
        print("   - Click 'Create Credentials' → 'OAuth client ID'")
        print("   - Select 'Desktop application'")
        print("   - Name it 'Voice Agent Gmail Integration'")
        print("   - Download the JSON file")
        print("5. Rename the downloaded file to 'client_secrets.json'")
        print(f"6. Place it in: {server_dir}")

        open_browser = input("\n🌐 Open Google Cloud Console now? (y/n): ").strip().lower()
        if open_browser == 'y':
            webbrowser.open('https://console.cloud.google.com/')

        print("\n⏳ Once you've downloaded the credentials file, press Enter to continue...")
        input()

        # Check again
        if check_file_exists(client_secrets_path, "OAuth2 credentials file"):
            print("✅ Great! OAuth2 credentials file found.")
        else:
            print("❌ Credentials file still not found. Please complete the setup and run this script again.")
            return False

    # Step 3: Update environment variables
    print_step(3, "Environment Configuration")

    env_updates = []

    if not google_secrets_file:
        env_updates.append("GOOGLE_CLIENT_SECRETS_FILE=client_secrets.json")
        print("✅ Adding GOOGLE_CLIENT_SECRETS_FILE to environment")

    env_updates.extend([
        "GMAIL_SEND_NOTIFICATIONS=true",
        "GMAIL_AUTO_CONFIRM_APPOINTMENTS=true"
    ])

    if env_updates:
        if env_exists:
            # Append to existing .env file
            with open(env_path, 'a') as f:
                f.write("\n# Gmail Integration Settings\n")
                for update in env_updates:
                    f.write(f"{update}\n")
            print(f"✅ Updated {env_path}")
        else:
            # Create new .env file
            with open(env_path, 'w') as f:
                f.write("# Gmail Integration Settings\n")
                for update in env_updates:
                    f.write(f"{update}\n")
            print(f"✅ Created {env_path}")

    # Step 4: Test authentication
    print_step(4, "Testing Gmail Authentication")

    try:
        # Add current directory to Python path
        sys.path.insert(0, str(server_dir / "src"))

        print("🔄 Testing Gmail service initialization...")
        from gmail_service import get_gmail_service

        gmail_service = get_gmail_service()
        profile = gmail_service.get_user_profile()

        if profile['success']:
            print(f"✅ Authentication successful!")
            print(f"   📧 Email: {profile['email']}")
            print(f"   📊 Total Messages: {profile['messages_total']}")
            print(f"   📂 Total Threads: {profile['threads_total']}")
        else:
            print(f"❌ Authentication failed: {profile['error']}")
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Installing required dependencies...")

        # Install dependencies
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                         cwd=server_dir, check=True, capture_output=True)
            print("✅ Dependencies installed successfully")

            # Try again
            from gmail_service import get_gmail_service
            gmail_service = get_gmail_service()
            profile = gmail_service.get_user_profile()

            if profile['success']:
                print(f"✅ Authentication successful!")
                print(f"   📧 Email: {profile['email']}")
            else:
                print(f"❌ Authentication failed: {profile['error']}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Step 5: Test email sending
    print_step(5, "Testing Email Functionality")

    test_email = input("📧 Enter your email address to send a test email (or press Enter to skip): ").strip()

    if test_email:
        try:
            result = gmail_service.send_simple_email(
                to=test_email,
                subject="✅ Voice Agent Setup Complete!",
                body="""
                <html>
                <body>
                    <h2>🎉 Congratulations!</h2>
                    <p>Your Gmail integration is working perfectly!</p>
                    <p>Your Renova Hospitals Voice Agent can now:</p>
                    <ul>
                        <li>Send appointment confirmation emails</li>
                        <li>Process voice email commands</li>
                        <li>Send notification emails</li>
                    </ul>
                    <p>Generated by the setup helper script.</p>
                </body>
                </html>
                """,
                is_html=True
            )

            if result['success']:
                print(f"✅ Test email sent successfully!")
                print(f"   📧 Message ID: {result['message_id']}")
            else:
                print(f"❌ Test email failed: {result['error']}")

        except Exception as e:
            print(f"❌ Error sending test email: {e}")

    # Step 6: Final status
    print_step(6, "Setup Complete!")

    print("🎉 Gmail integration is now set up and ready to use!")
    print("\n📋 What you can do now:")
    print("1. Start the enhanced server: python src/pipecat_server_enhanced.py")
    print("2. Test voice commands for appointment booking with email confirmation")
    print("3. Use the Gmail API endpoints for programmatic email sending")
    print("4. Send notification emails for call summaries and alerts")

    print("\n🔧 Available servers:")
    print("• Enhanced Server (with Gmail): python src/pipecat_server_enhanced.py")
    print("• Original Server: python src/pipecat_server.py")
    print("• Gmail Routes Only: Access via http://localhost:8090/gmail/")

    print("\n📚 Documentation:")
    print("• Setup Guide: GMAIL_SETUP.md")
    print("• Test Suite: python src/test_gmail_integration.py")
    print("• Examples: python src/gmail_examples.py")

    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🌟 Setup completed successfully!")
        else:
            print("\n⚠️  Setup incomplete. Please resolve the issues above.")
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")