import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Scopes define the permissions your app requests.
# Gmail scopes for appointment confirmation emails
# Calendar scopes for adding appointments to hospital calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

# The path to your credentials and token files
# Use absolute paths to avoid directory issues

# Get the server directory (one level up from src)
SERVER_DIR = Path(__file__).parent.parent

CLIENT_SECRETS_FILE = os.getenv(
    "GOOGLE_CLIENT_SECRETS_FILE",
    str(SERVER_DIR / "gclientsec.json.json")
)
TOKEN_PICKLE_FILE = str(SERVER_DIR / "google_token.pickle")

def get_credentials():
    """
    Handles the authentication flow.
    Loads existing credentials or prompts the user for new ones.
    """
    print(f"DEBUG: Looking for token file at: {TOKEN_PICKLE_FILE}")
    print(f"DEBUG: Token file exists: {os.path.exists(TOKEN_PICKLE_FILE)}")

    creds = None
    # Load the token from a file if it exists
    if os.path.exists(TOKEN_PICKLE_FILE):
        print("DEBUG: Loading existing token file...")
        with open(TOKEN_PICKLE_FILE, 'rb') as token:
            creds = pickle.load(token)
            print(f"DEBUG: Token loaded successfully")
            print(f"DEBUG: Token valid: {creds.valid if creds else 'None'}")
            print(f"DEBUG: Token expired: {creds.expired if creds else 'None'}")
            print(f"DEBUG: Has refresh token: {bool(creds.refresh_token) if creds else 'None'}")
            if creds and hasattr(creds, 'scopes'):
                print(f"DEBUG: Token scopes: {creds.scopes}")
    else:
        print("DEBUG: No existing token file found")

    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        print(f"DEBUG: Token needs refresh/recreation. creds exists: {bool(creds)}, valid: {creds.valid if creds else 'N/A'}")

        if creds and creds.expired and creds.refresh_token:
            print("DEBUG: Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("DEBUG: Token refreshed successfully")
            except Exception as e:
                print(f"DEBUG: Token refresh failed: {e}")
                creds = None
        else:
            print(f"DEBUG: Need new OAuth flow. Reasons:")
            print(f"   - No creds: {not creds}")
            print(f"   - No refresh token: {not (creds and creds.refresh_token) if creds else 'N/A'}")
            print(f"   - Not expired: {not (creds and creds.expired) if creds else 'N/A'}")

            # Check if credentials file exists
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"DEBUG: Credentials file not found at: {CLIENT_SECRETS_FILE}")
                raise FileNotFoundError(
                    f"Google credentials file not found!\n"
                    f"Expected location: {CLIENT_SECRETS_FILE}\n"
                    f"Current working directory: {os.getcwd()}\n"
                    f"Please copy your Google credentials file to: {CLIENT_SECRETS_FILE}\n"
                    f"or set the GOOGLE_CLIENT_SECRETS_FILE environment variable to the correct path."
                )

            print(f"DEBUG: Starting OAuth2 flow using credentials from: {CLIENT_SECRETS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=61538)
            print("DEBUG: New token obtained successfully")

        # Save the credentials for the next run
        print(f"DEBUG: Saving token to: {TOKEN_PICKLE_FILE}")
        with open(TOKEN_PICKLE_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print("DEBUG: Token saved successfully")

    print("DEBUG: Returning valid credentials")
    return creds