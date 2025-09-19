#!/usr/bin/env python3

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class PatientRecord:
    """Represents a patient record"""
    phone: str
    name: str = ""
    email: str = ""
    last_visit: str = ""
    preferred_doctor: str = ""
    department: str = ""
    language: str = "english"
    customer_type: str = "unknown"
    notes: str = ""
    created: str = ""
    updated: str = ""

@dataclass
class CallLogRecord:
    """Represents a call log record"""
    call_id: str
    timestamp: str
    phone: str
    name: str = ""
    duration: int = 0
    language: str = "english"
    call_type: str = "general"
    department: str = ""
    doctor: str = ""
    status: str = "completed"
    resolution: str = "resolved"
    notes: str = ""

class GoogleSheetsService:
    """Google Sheets service for managing patient data and call logs"""

    def __init__(self, credentials=None):
        self.drive_service = None
        self.sheets_service = None
        self.credentials = credentials
        self.voice_agent_folder_id = None
        self.patient_sheet_id = None
        self.calllog_sheet_id = None
        self._initialize_services()

    def _initialize_services(self):
        """Initialize Google Drive and Sheets services"""
        try:
            if self.credentials:
                creds = self.credentials
            else:
                from googel_auth_manger import get_credentials
                creds = get_credentials()

            self.drive_service = build('drive', 'v3', credentials=creds)
            self.sheets_service = build('sheets', 'v4', credentials=creds)

            logger.info("Google Drive and Sheets services initialized successfully")

            # Initialize folder and sheets
            self._ensure_voice_agent_setup()

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            raise

    def _ensure_voice_agent_setup(self):
        """Ensure VoiceAgent folder and sheets exist"""
        try:
            # Check/create VoiceAgent folder
            self._ensure_voice_agent_folder()

            # Check/create PatientData sheet
            self._ensure_patient_sheet()

            # Check/create CallLog sheet
            self._ensure_calllog_sheet()

            logger.info("VoiceAgent folder and sheets setup completed")

        except Exception as e:
            logger.error(f"Failed to setup VoiceAgent folder and sheets: {e}")
            raise

    def _ensure_voice_agent_folder(self):
        """Ensure VoiceAgent folder exists, create if not"""
        try:
            # Search for existing VoiceAgent folder
            query = "name='VoiceAgent' and mimeType='application/vnd.google-apps.folder'"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])

            if folders:
                self.voice_agent_folder_id = folders[0]['id']
                logger.info(f"Found existing VoiceAgent folder: {self.voice_agent_folder_id}")
            else:
                # Create VoiceAgent folder
                folder_metadata = {
                    'name': 'VoiceAgent',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
                self.voice_agent_folder_id = folder.get('id')
                logger.info(f"Created VoiceAgent folder: {self.voice_agent_folder_id}")

        except Exception as e:
            logger.error(f"Failed to ensure VoiceAgent folder: {e}")
            raise

    def _ensure_patient_sheet(self):
        """Ensure PatientData sheet exists, create if not"""
        try:
            # Search for existing PatientData sheet in VoiceAgent folder
            query = f"name='PatientData' and '{self.voice_agent_folder_id}' in parents"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            sheets = results.get('files', [])

            if sheets:
                self.patient_sheet_id = sheets[0]['id']
                logger.info(f"Found existing PatientData sheet: {self.patient_sheet_id}")
            else:
                # Create PatientData sheet
                self.patient_sheet_id = self._create_patient_sheet()
                logger.info(f"Created PatientData sheet: {self.patient_sheet_id}")

        except Exception as e:
            logger.error(f"Failed to ensure PatientData sheet: {e}")
            raise

    def _ensure_calllog_sheet(self):
        """Ensure CallLog sheet exists, create if not"""
        try:
            # Search for existing CallLog sheet in VoiceAgent folder
            query = f"name='CallLog' and '{self.voice_agent_folder_id}' in parents"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            sheets = results.get('files', [])

            if sheets:
                self.calllog_sheet_id = sheets[0]['id']
                logger.info(f"Found existing CallLog sheet: {self.calllog_sheet_id}")
            else:
                # Create CallLog sheet
                self.calllog_sheet_id = self._create_calllog_sheet()
                logger.info(f"Created CallLog sheet: {self.calllog_sheet_id}")

        except Exception as e:
            logger.error(f"Failed to ensure CallLog sheet: {e}")
            raise

    def _create_patient_sheet(self) -> str:
        """Create PatientData sheet with headers"""
        try:
            # Create spreadsheet
            sheet_metadata = {
                'properties': {
                    'title': 'PatientData'
                },
                'sheets': [{
                    'properties': {
                        'title': 'Patients'
                    }
                }]
            }

            sheet = self.sheets_service.spreadsheets().create(body=sheet_metadata).execute()
            sheet_id = sheet.get('spreadsheetId')

            # Move to VoiceAgent folder
            self.drive_service.files().update(
                fileId=sheet_id,
                addParents=self.voice_agent_folder_id,
                fields='id, parents'
            ).execute()

            # Add headers
            headers = [
                'Phone', 'Name', 'Email', 'Last_Visit', 'Preferred_Doctor',
                'Department', 'Language', 'Customer_Type', 'Notes', 'Created', 'Updated'
            ]

            body = {
                'values': [headers]
            }

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='Patients!A1:K1',
                valueInputOption='RAW',
                body=body
            ).execute()

            # Format headers (bold)
            format_request = {
                'requests': [{
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat.bold'
                    }
                }]
            }

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body=format_request
            ).execute()

            logger.info(f"Created PatientData sheet with headers: {sheet_id}")
            return sheet_id

        except Exception as e:
            logger.error(f"Failed to create PatientData sheet: {e}")
            raise

    def _create_calllog_sheet(self) -> str:
        """Create CallLog sheet with headers"""
        try:
            # Create spreadsheet
            sheet_metadata = {
                'properties': {
                    'title': 'CallLog'
                },
                'sheets': [{
                    'properties': {
                        'title': 'Calls'
                    }
                }]
            }

            sheet = self.sheets_service.spreadsheets().create(body=sheet_metadata).execute()
            sheet_id = sheet.get('spreadsheetId')

            # Move to VoiceAgent folder
            self.drive_service.files().update(
                fileId=sheet_id,
                addParents=self.voice_agent_folder_id,
                fields='id, parents'
            ).execute()

            # Add headers
            headers = [
                'Call_ID', 'Timestamp', 'Phone', 'Name', 'Duration_Seconds', 'Language',
                'Call_Type', 'Department', 'Doctor', 'Status', 'Resolution', 'Notes'
            ]

            body = {
                'values': [headers]
            }

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='Calls!A1:L1',
                valueInputOption='RAW',
                body=body
            ).execute()

            # Format headers (bold)
            format_request = {
                'requests': [{
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat.bold'
                    }
                }]
            }

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body=format_request
            ).execute()

            logger.info(f"Created CallLog sheet with headers: {sheet_id}")
            return sheet_id

        except Exception as e:
            logger.error(f"Failed to create CallLog sheet: {e}")
            raise

    def get_patient_by_phone(self, phone: str) -> Optional[PatientRecord]:
        """Retrieve patient by phone number"""
        try:
            if not self.patient_sheet_id:
                logger.warning("PatientData sheet not available")
                return None

            # Get all patient data
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.patient_sheet_id,
                range='Patients!A:K'
            ).execute()

            values = result.get('values', [])
            if not values or len(values) <= 1:  # Only headers or empty
                return None

            # Search for phone number (first column)
            for row in values[1:]:  # Skip header
                if row and len(row) > 0 and row[0] == phone:
                    # Convert row to PatientRecord
                    return PatientRecord(
                        phone=row[0] if len(row) > 0 else "",
                        name=row[1] if len(row) > 1 else "",
                        email=row[2] if len(row) > 2 else "",
                        last_visit=row[3] if len(row) > 3 else "",
                        preferred_doctor=row[4] if len(row) > 4 else "",
                        department=row[5] if len(row) > 5 else "",
                        language=row[6] if len(row) > 6 else "english",
                        customer_type=row[7] if len(row) > 7 else "unknown",
                        notes=row[8] if len(row) > 8 else "",
                        created=row[9] if len(row) > 9 else "",
                        updated=row[10] if len(row) > 10 else ""
                    )

            return None

        except Exception as e:
            logger.error(f"Failed to get patient by phone {phone}: {e}")
            return None

    def save_patient_data(self, patient: PatientRecord) -> bool:
        """Save or update patient data"""
        try:
            if not self.patient_sheet_id:
                logger.error("PatientData sheet not available")
                return False

            # Check if patient exists
            existing_patient = self.get_patient_by_phone(patient.phone)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            patient_row = [
                patient.phone,
                patient.name,
                patient.email,
                patient.last_visit or current_time,
                patient.preferred_doctor,
                patient.department,
                patient.language,
                patient.customer_type,
                patient.notes,
                patient.created or current_time,
                current_time  # Always update the "updated" timestamp
            ]

            if existing_patient:
                # Update existing patient - find row and update
                self._update_patient_row(patient.phone, patient_row)
                logger.info(f"Updated patient data for: {patient.phone}")
            else:
                # Add new patient
                body = {
                    'values': [patient_row]
                }

                self.sheets_service.spreadsheets().values().append(
                    spreadsheetId=self.patient_sheet_id,
                    range='Patients!A:K',
                    valueInputOption='RAW',
                    body=body
                ).execute()

                logger.info(f"Added new patient data for: {patient.phone}")

            return True

        except Exception as e:
            logger.error(f"Failed to save patient data for {patient.phone}: {e}")
            return False

    def _update_patient_row(self, phone: str, patient_row: List[str]):
        """Update existing patient row"""
        try:
            # Get all data to find the row
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.patient_sheet_id,
                range='Patients!A:K'
            ).execute()

            values = result.get('values', [])

            # Find the row with matching phone
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (skip header)
                if row and len(row) > 0 and row[0] == phone:
                    # Update this row
                    range_name = f'Patients!A{i}:K{i}'
                    body = {
                        'values': [patient_row]
                    }

                    self.sheets_service.spreadsheets().values().update(
                        spreadsheetId=self.patient_sheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    break

        except Exception as e:
            logger.error(f"Failed to update patient row for {phone}: {e}")
            raise

    def log_call_record(self, call_log: CallLogRecord) -> bool:
        """Add call log entry (mandatory at end of every call)"""
        try:
            if not self.calllog_sheet_id:
                logger.error("CallLog sheet not available")
                return False

            call_row = [
                call_log.call_id,
                call_log.timestamp,
                call_log.phone,
                call_log.name,
                str(call_log.duration),
                call_log.language,
                call_log.call_type,
                call_log.department,
                call_log.doctor,
                call_log.status,
                call_log.resolution,
                call_log.notes
            ]

            body = {
                'values': [call_row]
            }

            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.calllog_sheet_id,
                range='Calls!A:L',
                valueInputOption='RAW',
                body=body
            ).execute()

            logger.info(f"Logged call record: {call_log.call_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to log call record {call_log.call_id}: {e}")
            return False

    def search_patients(self, criteria: Dict[str, str]) -> List[PatientRecord]:
        """Search patients by criteria"""
        try:
            if not self.patient_sheet_id:
                return []

            # Get all patient data
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.patient_sheet_id,
                range='Patients!A:K'
            ).execute()

            values = result.get('values', [])
            if not values or len(values) <= 1:
                return []

            matching_patients = []

            for row in values[1:]:  # Skip header
                if not row:
                    continue

                patient = PatientRecord(
                    phone=row[0] if len(row) > 0 else "",
                    name=row[1] if len(row) > 1 else "",
                    email=row[2] if len(row) > 2 else "",
                    last_visit=row[3] if len(row) > 3 else "",
                    preferred_doctor=row[4] if len(row) > 4 else "",
                    department=row[5] if len(row) > 5 else "",
                    language=row[6] if len(row) > 6 else "english",
                    customer_type=row[7] if len(row) > 7 else "unknown",
                    notes=row[8] if len(row) > 8 else "",
                    created=row[9] if len(row) > 9 else "",
                    updated=row[10] if len(row) > 10 else ""
                )

                # Check if patient matches criteria
                matches = True
                for key, value in criteria.items():
                    patient_value = getattr(patient, key, "").lower()
                    if value.lower() not in patient_value:
                        matches = False
                        break

                if matches:
                    matching_patients.append(patient)

            return matching_patients

        except Exception as e:
            logger.error(f"Failed to search patients: {e}")
            return []

    def get_call_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get call analytics for the last N days"""
        try:
            if not self.calllog_sheet_id:
                return {}

            # Get all call data
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.calllog_sheet_id,
                range='Calls!A:L'
            ).execute()

            values = result.get('values', [])
            if not values or len(values) <= 1:
                return {}

            # Calculate analytics
            analytics = {
                'total_calls': len(values) - 1,  # Exclude header
                'by_language': {},
                'by_department': {},
                'by_status': {},
                'average_duration': 0
            }

            total_duration = 0
            for row in values[1:]:  # Skip header
                if len(row) < 6:
                    continue

                # Count by language
                language = row[5] if len(row) > 5 else "unknown"
                analytics['by_language'][language] = analytics['by_language'].get(language, 0) + 1

                # Count by department
                department = row[7] if len(row) > 7 else "unknown"
                analytics['by_department'][department] = analytics['by_department'].get(department, 0) + 1

                # Count by status
                status = row[9] if len(row) > 9 else "unknown"
                analytics['by_status'][status] = analytics['by_status'].get(status, 0) + 1

                # Calculate duration
                try:
                    duration = int(row[4]) if len(row) > 4 and row[4].isdigit() else 0
                    total_duration += duration
                except:
                    pass

            if analytics['total_calls'] > 0:
                analytics['average_duration'] = total_duration / analytics['total_calls']

            return analytics

        except Exception as e:
            logger.error(f"Failed to get call analytics: {e}")
            return {}

    def get_recent_call_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent call logs from Google Sheets"""
        try:
            if not self.calllog_sheet_id:
                logger.warning("CallLog sheet not initialized yet")
                return []

            # Get all call data (we'll limit on our side)
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.calllog_sheet_id,
                range='Calls!A:L'
            ).execute()

            values = result.get('values', [])
            if not values or len(values) <= 1:
                return []

            # Headers for reference: Call ID, Timestamp, Phone, Name, Duration, Language,
            # Call Type, Department, Doctor, Status, Resolution, Notes
            headers = values[0] if values else []
            call_logs = []

            # Process rows (skip header), take most recent first
            data_rows = values[1:] if len(values) > 1 else []
            # Reverse to get most recent first (assuming they're added chronologically)
            recent_rows = list(reversed(data_rows))[:limit]

            for row in recent_rows:
                if len(row) >= 4:  # At least have basic info
                    call_log = {
                        'call_id': row[0] if len(row) > 0 else '',
                        'timestamp': row[1] if len(row) > 1 else '',
                        'phone': row[2] if len(row) > 2 else '',
                        'name': row[3] if len(row) > 3 else '',
                        'duration': row[4] if len(row) > 4 else '0',
                        'language': row[5] if len(row) > 5 else 'english',
                        'call_type': row[6] if len(row) > 6 else '',
                        'department': row[7] if len(row) > 7 else '',
                        'doctor': row[8] if len(row) > 8 else '',
                        'status': row[9] if len(row) > 9 else '',
                        'resolution': row[10] if len(row) > 10 else '',
                        'notes': row[11] if len(row) > 11 else ''
                    }
                    call_logs.append(call_log)

            logger.info(f"Retrieved {len(call_logs)} call logs from Google Sheets")
            return call_logs

        except Exception as e:
            logger.error(f"Failed to get recent call logs from Sheets: {e}")
            # If the sheet exists but has no data, try to initialize it
            if "Unable to parse range" in str(e):
                logger.info("Sheet exists but may be empty, returning empty list")
            return []

# Global instance
_sheets_service = None

def get_sheets_service(credentials=None) -> GoogleSheetsService:
    """Get singleton GoogleSheetsService instance"""
    global _sheets_service
    if _sheets_service is None:
        _sheets_service = GoogleSheetsService(credentials)
    return _sheets_service

# Test function
if __name__ == "__main__":
    # Test the sheets service
    service = GoogleSheetsService()
    print("Google Sheets service initialized successfully")