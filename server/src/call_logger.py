#!/usr/bin/env python3

import os
import csv
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Set up logging
logger = logging.getLogger(__name__)

class CallType(Enum):
    """Types of calls"""
    APPOINTMENT_BOOKING = "appointment_booking"
    APPOINTMENT_CANCELLATION = "appointment_cancellation"
    GENERAL_ENQUIRY = "general_enquiry"
    DEPARTMENT_ENQUIRY = "department_enquiry"
    DOCTOR_ENQUIRY = "doctor_enquiry"
    BILLING_ENQUIRY = "billing_enquiry"
    EMERGENCY = "emergency"
    OTHER = "other"

class CustomerType(Enum):
    """Customer types"""
    NEW = "new"
    EXISTING = "existing"
    UNKNOWN = "unknown"

class CallStatus(Enum):
    """Call resolution status"""
    RESOLVED = "resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    UNRESOLVED = "unresolved"
    ESCALATED = "escalated"
    FOLLOW_UP_REQUIRED = "follow_up_required"

@dataclass
class CallRecord:
    """Represents a call record"""
    call_id: str
    timestamp: str
    caller_phone: str
    duration_seconds: Optional[int]
    customer_type: str
    customer_name: str
    customer_email: str
    call_type: str
    department_enquired: str
    doctor_enquired: str
    appointment_date: Optional[str]
    appointment_time: Optional[str]
    language_used: str
    call_summary: str
    resolution_status: str
    agent_notes: str
    session_id: Optional[str] = None
    hangup_reason: Optional[str] = None

class CallLogger:
    """Handles logging of call information to CSV"""

    def __init__(self, csv_file_path: str = None):
        """Initialize the call logger"""
        self.csv_file_path = csv_file_path or os.path.join(
            os.path.dirname(__file__), '..', 'call_logs.csv'
        )
        self.ensure_csv_exists()

    def ensure_csv_exists(self):
        """Ensure the CSV file exists with proper headers"""
        if not os.path.exists(self.csv_file_path):
            try:
                os.makedirs(os.path.dirname(self.csv_file_path), exist_ok=True)

                # Create CSV with headers
                with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        'call_id', 'timestamp', 'caller_phone', 'duration_seconds',
                        'customer_type', 'customer_name', 'customer_email',
                        'call_type', 'department_enquired', 'doctor_enquired',
                        'appointment_date', 'appointment_time', 'language_used',
                        'call_summary', 'resolution_status', 'agent_notes',
                        'session_id', 'hangup_reason'
                    ])
                logger.info(f"Created new call log CSV: {self.csv_file_path}")

            except Exception as e:
                logger.error(f"Failed to create CSV file: {e}")
                raise

    def log_call(self, call_data: Dict[str, Any]) -> str:
        """Log a call to the CSV file"""
        try:
            # Generate unique call ID
            call_id = call_data.get('call_id', str(uuid.uuid4())[:8])

            # Create call record
            record = CallRecord(
                call_id=call_id,
                timestamp=call_data.get('timestamp', datetime.now().isoformat()),
                caller_phone=call_data.get('caller_phone', 'unknown'),
                duration_seconds=call_data.get('duration_seconds'),
                customer_type=call_data.get('customer_type', CustomerType.UNKNOWN.value),
                customer_name=call_data.get('customer_name', ''),
                customer_email=call_data.get('customer_email', ''),
                call_type=call_data.get('call_type', CallType.OTHER.value),
                department_enquired=call_data.get('department_enquired', ''),
                doctor_enquired=call_data.get('doctor_enquired', ''),
                appointment_date=call_data.get('appointment_date'),
                appointment_time=call_data.get('appointment_time'),
                language_used=call_data.get('language_used', 'english'),
                call_summary=call_data.get('call_summary', ''),
                resolution_status=call_data.get('resolution_status', CallStatus.UNRESOLVED.value),
                agent_notes=call_data.get('agent_notes', ''),
                session_id=call_data.get('session_id'),
                hangup_reason=call_data.get('hangup_reason')
            )

            # Write to CSV
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    record.call_id, record.timestamp, record.caller_phone, record.duration_seconds,
                    record.customer_type, record.customer_name, record.customer_email,
                    record.call_type, record.department_enquired, record.doctor_enquired,
                    record.appointment_date, record.appointment_time, record.language_used,
                    record.call_summary, record.resolution_status, record.agent_notes,
                    record.session_id, record.hangup_reason
                ])

            logger.info(f"Call logged successfully: {call_id}")
            return call_id

        except Exception as e:
            logger.error(f"Failed to log call: {e}")
            raise

    def update_call(self, call_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing call record"""
        try:
            # Read all records
            records = []
            updated = False

            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                records = list(reader)

            # Update the matching record
            for record in records:
                if record['call_id'] == call_id:
                    for key, value in updates.items():
                        if key in record:
                            record[key] = str(value) if value is not None else ''
                    updated = True
                    break

            if not updated:
                logger.warning(f"Call ID not found for update: {call_id}")
                return False

            # Write back to CSV
            with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as file:
                if records:
                    writer = csv.DictWriter(file, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)

            logger.info(f"Call updated successfully: {call_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update call: {e}")
            return False

    def get_call_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get call statistics for the last N days"""
        try:
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            stats = {
                'total_calls': 0,
                'by_type': {},
                'by_language': {},
                'by_resolution': {},
                'by_customer_type': {},
                'average_duration': 0,
                'departments_contacted': {},
                'doctors_contacted': {}
            }

            durations = []

            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for record in reader:
                    # Filter by date
                    if record['timestamp'] < cutoff_date:
                        continue

                    stats['total_calls'] += 1

                    # Count by type
                    call_type = record['call_type']
                    stats['by_type'][call_type] = stats['by_type'].get(call_type, 0) + 1

                    # Count by language
                    language = record['language_used']
                    stats['by_language'][language] = stats['by_language'].get(language, 0) + 1

                    # Count by resolution
                    resolution = record['resolution_status']
                    stats['by_resolution'][resolution] = stats['by_resolution'].get(resolution, 0) + 1

                    # Count by customer type
                    customer_type = record['customer_type']
                    stats['by_customer_type'][customer_type] = stats['by_customer_type'].get(customer_type, 0) + 1

                    # Track departments
                    if record['department_enquired']:
                        dept = record['department_enquired']
                        stats['departments_contacted'][dept] = stats['departments_contacted'].get(dept, 0) + 1

                    # Track doctors
                    if record['doctor_enquired']:
                        doctor = record['doctor_enquired']
                        stats['doctors_contacted'][doctor] = stats['doctors_contacted'].get(doctor, 0) + 1

                    # Collect durations
                    if record['duration_seconds']:
                        try:
                            durations.append(int(record['duration_seconds']))
                        except ValueError:
                            pass

            # Calculate average duration
            if durations:
                stats['average_duration'] = sum(durations) / len(durations)

            return stats

        except Exception as e:
            logger.error(f"Failed to get call stats: {e}")
            return {}

    def search_calls(self, **criteria) -> list:
        """Search calls by various criteria"""
        try:
            matching_calls = []

            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for record in reader:
                    match = True

                    for key, value in criteria.items():
                        if key in record:
                            if isinstance(value, str):
                                if value.lower() not in record[key].lower():
                                    match = False
                                    break
                            else:
                                if str(value) != record[key]:
                                    match = False
                                    break

                    if match:
                        matching_calls.append(record)

            return matching_calls

        except Exception as e:
            logger.error(f"Failed to search calls: {e}")
            return []

    def get_recent_calls(self, limit: int = 50) -> list:
        """Get recent call logs from CSV"""
        try:
            if not os.path.exists(self.csv_file_path):
                return []

            calls = []
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    calls.append(row)

            # Return most recent calls (reverse order)
            return calls[-limit:] if len(calls) > limit else calls

        except Exception as e:
            logger.error(f"Failed to read recent calls: {str(e)}")
            return []

# Global call logger instance
_call_logger = None

def get_call_logger() -> CallLogger:
    """Get a singleton CallLogger instance"""
    global _call_logger
    if _call_logger is None:
        _call_logger = CallLogger()
    return _call_logger

def log_call_quick(call_type: str, customer_name: str, customer_phone: str,
                   summary: str, **kwargs) -> str:
    """Quick function to log a call"""
    try:
        logger_instance = get_call_logger()

        call_data = {
            'call_type': call_type,
            'customer_name': customer_name,
            'caller_phone': customer_phone,
            'call_summary': summary,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }

        return logger_instance.log_call(call_data)

    except Exception as e:
        logger.error(f"Quick call logging failed: {e}")
        return ''

# Test function
if __name__ == "__main__":
    # Test the call logger
    logger_instance = CallLogger()

    # Test logging a call
    test_call = {
        'call_type': CallType.APPOINTMENT_BOOKING.value,
        'customer_name': 'Test Patient',
        'caller_phone': '+91-9876543210',
        'customer_email': 'test@example.com',
        'customer_type': CustomerType.NEW.value,
        'department_enquired': 'Cardiology',
        'doctor_enquired': 'Dr. Sharma',
        'appointment_date': '2024-12-25',
        'appointment_time': '10:00 AM',
        'language_used': 'english',
        'call_summary': 'Patient called to book appointment with cardiologist',
        'resolution_status': CallStatus.RESOLVED.value,
        'agent_notes': 'Appointment successfully booked'
    }

    call_id = logger_instance.log_call(test_call)
    print(f"Test call logged with ID: {call_id}")

    # Test getting stats
    stats = logger_instance.get_call_stats(30)
    print(f"Call statistics: {stats}")