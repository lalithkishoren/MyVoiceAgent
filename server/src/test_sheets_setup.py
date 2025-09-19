#!/usr/bin/env python3

import sys
from datetime import datetime
from googel_auth_manger import get_credentials
from google_sheets_service import GoogleSheetsService, PatientRecord, CallLogRecord

def test_sheets_setup():
    """Test Google Sheets setup and insert sample records"""
    print("Testing Google Sheets setup...")

    try:
        # Initialize credentials and service
        print("1. Getting Google credentials...")
        creds = get_credentials()
        print("SUCCESS: Credentials obtained successfully")

        # Initialize Google Sheets service
        print("2. Initializing Google Sheets service...")
        sheets_service = GoogleSheetsService(creds)
        print("SUCCESS: Google Sheets service initialized")

        # Test patient data insertion
        print("\n3. Testing PatientData sheet...")
        sample_patient = PatientRecord(
            phone="1234567890",
            name="Test Patient",
            email="test@example.com",
            last_visit=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            preferred_doctor="Dr. Smith",
            department="General Medicine",
            language="english",
            customer_type="new",
            notes="Test patient record"
        )

        result = sheets_service.save_patient_data(sample_patient)
        if result:
            print("SUCCESS: Sample patient data saved successfully")
        else:
            print("ERROR: Failed to save patient data")

        # Test call log insertion
        print("\n4. Testing CallLog sheet...")
        sample_call = CallLogRecord(
            call_id="test-call-001",
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            phone="1234567890",
            name="Test Patient",
            duration=120,
            language="english",
            call_type="appointment_booking",
            department="General Medicine",
            doctor="Dr. Smith",
            status="completed",
            resolution="Appointment booked successfully",
            notes="Test call record"
        )

        result = sheets_service.log_call_record(sample_call)
        if result:
            print("SUCCESS: Sample call log saved successfully")
        else:
            print("ERROR: Failed to save call log")

        # Test reading data back
        print("\n5. Testing data retrieval...")

        # Test patient retrieval
        patient = sheets_service.get_patient_by_phone("1234567890")
        if patient:
            print(f"SUCCESS: Patient retrieved: {patient.name} ({patient.email})")
        else:
            print("ERROR: Failed to retrieve patient")

        # Test call logs retrieval
        call_logs = sheets_service.get_recent_call_logs(limit=5)
        print(f"SUCCESS: Retrieved {len(call_logs)} call logs")
        if call_logs:
            print(f"   Latest call: {call_logs[0].get('call_id', 'Unknown')} - {call_logs[0].get('name', 'Unknown')}")

        print("\nSUCCESS: Google Sheets integration test completed successfully!")
        return True

    except Exception as e:
        print(f"ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sheets_setup()
    sys.exit(0 if success else 1)