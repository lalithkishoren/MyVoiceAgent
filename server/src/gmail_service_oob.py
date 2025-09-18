import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

# Scopes for Gmail API
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

# File paths
CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "../gclientsec.json.json")
TOKEN_PICKLE_FILE = "google_token.pickle"

def get_credentials_oob():
    """
    Get credentials using Out-of-Band (OOB) flow
    This avoids the random port issue
    """
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_PICKLE_FILE):
        with open(TOKEN_PICKLE_FILE, 'rb') as token:
            creds = pickle.load(token)

    # Check if credentials are valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing access token...")
            creds.refresh(Request())
        else:
            print("Starting OAuth2 flow with Out-of-Band method...")
            print("This will open a browser and ask you to copy/paste a code.")

            # Use OOB flow instead of local server
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # OOB flow
            )

            # Get authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')

            print(f"\nPlease go to this URL and authorize the application:")
            print(f"{auth_url}")
            print(f"\nAfter authorization, copy the code from the browser and paste it here:")

            # Get authorization code from user
            code = input("Enter authorization code: ").strip()

            # Exchange code for token
            flow.fetch_token(code=code)
            creds = flow.credentials

        # Save credentials
        with open(TOKEN_PICKLE_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds

def test_gmail_oob():
    """Test Gmail API with OOB authentication"""
    try:
        creds = get_credentials_oob()

        if creds and creds.valid:
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)

            # Test with profile
            profile = service.users().getProfile(userId='me').execute()

            print(f"SUCCESS: Gmail authentication working!")
            print(f"Email: {profile['emailAddress']}")
            print(f"Messages: {profile['messagesTotal']}")
            print(f"Threads: {profile['threadsTotal']}")

            return True

        else:
            print("FAILED: Could not get valid credentials")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing Gmail with Out-of-Band OAuth2 flow...")
    print("This avoids the random port redirect issue.")
    print("=" * 50)

    success = test_gmail_oob()

    if success:
        print("\nGmail integration is working!")
        print("You can now use the voice agent with email features.")
    else:
        print("\nGmail integration failed.")
        print("Check your credentials and try again.")