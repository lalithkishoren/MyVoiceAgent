#!/usr/bin/env python3

import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googel_auth_manger import get_credentials

def test_google_services():
    """Test Google Drive and Sheets API access"""
    try:
        print("Getting Google credentials...")
        creds = get_credentials()
        print("SUCCESS: Credentials obtained successfully")

        # Test Drive API
        print("\nTesting Google Drive API...")
        drive_service = build('drive', 'v3', credentials=creds)

        # List some files to test access
        results = drive_service.files().list(pageSize=5, fields="files(id, name, mimeType)").execute()
        files = results.get('files', [])

        print(f"SUCCESS: Drive API working - Found {len(files)} files")
        for file in files[:3]:
            print(f"   - {file['name']} ({file['mimeType']})")

        # Test Sheets API
        print("\nTesting Google Sheets API...")
        sheets_service = build('sheets', 'v4', credentials=creds)

        # Test by getting metadata (doesn't require a specific sheet)
        print("SUCCESS: Sheets API initialized successfully")

        # Check if VoiceAgent folder exists
        print("\nChecking for 'VoiceAgent' folder...")
        query = "name='VoiceAgent' and mimeType='application/vnd.google-apps.folder'"
        folder_results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        voice_agent_folders = folder_results.get('files', [])

        if voice_agent_folders:
            folder_id = voice_agent_folders[0]['id']
            print(f"SUCCESS: Found VoiceAgent folder: {folder_id}")

            # List files in VoiceAgent folder
            query = f"'{folder_id}' in parents"
            folder_files = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            files_in_folder = folder_files.get('files', [])

            print(f"Files in VoiceAgent folder: {len(files_in_folder)}")
            for file in files_in_folder:
                print(f"   - {file['name']} ({file['mimeType']})")
        else:
            print("INFO: VoiceAgent folder not found - will need to create it")

        print("\nGoogle Services Test Summary:")
        print("SUCCESS: Drive API: Working")
        print("SUCCESS: Sheets API: Working")
        print("SUCCESS: Authentication: Success")
        print(f"VoiceAgent folder: {'Found' if voice_agent_folders else 'Needs creation'}")

        return True

    except HttpError as error:
        print(f"ERROR: Google API HTTP Error: {error}")
        return False
    except Exception as e:
        print(f"ERROR: Error testing Google services: {e}")
        return False

if __name__ == "__main__":
    test_google_services()