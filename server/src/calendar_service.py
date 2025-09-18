#!/usr/bin/env python3

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from googel_auth_manger import get_credentials

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class CalendarEvent:
    """Represents a calendar event"""
    summary: str
    description: str
    start_datetime: datetime
    end_datetime: datetime
    attendee_email: Optional[str] = None
    location: Optional[str] = None

class CalendarService:
    """Google Calendar API service for managing hospital appointments"""

    def __init__(self):
        self.service = None
        self.calendar_id = 'primary'  # Use primary calendar for hospital appointments
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the Google Calendar API service with authentication"""
        try:
            creds = get_credentials()
            self.service = build('calendar', 'v3', credentials=creds)

            # Test the service by getting calendar info
            calendar = self.service.calendars().get(calendarId=self.calendar_id).execute()
            logger.info(f"Calendar service initialized successfully for: {calendar.get('summary', 'Primary Calendar')}")

        except Exception as e:
            logger.error(f"Failed to initialize Calendar service: {str(e)}")
            raise

    def create_appointment_event(self, patient_name: str, patient_email: str, patient_phone: str,
                               appointment_date: str, appointment_time: str,
                               doctor_name: str, department: str) -> Dict[str, Any]:
        """Create a calendar event for the appointment"""
        try:
            if not self.service:
                raise Exception("Calendar service not initialized")

            # Parse appointment date and time
            start_datetime = self._parse_appointment_datetime(appointment_date, appointment_time)
            if not start_datetime:
                return {
                    'success': False,
                    'error': f'Invalid date/time format: {appointment_date} {appointment_time}'
                }

            # Calculate end time (default 30 minutes)
            end_datetime = start_datetime + timedelta(minutes=30)

            # Create event object
            event = {
                'summary': f'Appointment: {patient_name} - {doctor_name}',
                'description': f"""
Renova Hospitals Appointment

Patient: {patient_name}
Phone: {patient_phone}
Email: {patient_email}
Doctor: {doctor_name}
Department: {department}

Automatically scheduled via voice agent.
                """.strip(),
                'location': 'Renova Hospitals',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',  # India timezone
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',  # India timezone
                },
                'attendees': [
                    {'email': patient_email},
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 10},       # 10 minutes before
                    ],
                },
                'colorId': '2',  # Green color for appointments
            }

            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()

            logger.info(f"Calendar event created successfully. Event ID: {created_event['id']}")
            logger.info(f"Appointment: {patient_name} with {doctor_name} on {appointment_date} at {appointment_time}")

            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink', ''),
                'patient': patient_name,
                'doctor': doctor_name,
                'date': appointment_date,
                'time': appointment_time,
                'message': f'Appointment added to hospital calendar: {patient_name} with {doctor_name}'
            }

        except HttpError as error:
            logger.error(f"Calendar API HTTP error: {error}")
            return {
                'success': False,
                'error': f"Calendar API error: {error}",
                'error_code': error.resp.status if error.resp else None
            }
        except Exception as e:
            logger.error(f"Failed to create calendar event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_appointment_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse appointment date and time strings into datetime object"""
        try:
            # Common date formats to try
            date_formats = [
                "%Y-%m-%d",     # 2024-01-15
                "%m/%d/%Y",     # 01/15/2024
                "%B %d, %Y",    # January 15, 2024
                "%b %d, %Y",    # Jan 15, 2024
                "%d-%m-%Y",     # 15-01-2024
            ]

            # Common time formats to try
            time_formats = [
                "%H:%M",        # 14:30
                "%I:%M %p",     # 2:30 PM
                "%I:%M%p",      # 2:30PM
                "%H:%M:%S",     # 14:30:00
            ]

            parsed_date = None
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), date_format).date()
                    break
                except ValueError:
                    continue

            if not parsed_date:
                logger.error(f"Could not parse date: {date_str}")
                return None

            parsed_time = None
            for time_format in time_formats:
                try:
                    parsed_time = datetime.strptime(time_str.strip(), time_format).time()
                    break
                except ValueError:
                    continue

            if not parsed_time:
                logger.error(f"Could not parse time: {time_str}")
                return None

            # Combine date and time
            appointment_datetime = datetime.combine(parsed_date, parsed_time)
            return appointment_datetime

        except Exception as e:
            logger.error(f"Error parsing appointment datetime: {e}")
            return None

    def list_upcoming_appointments(self, days_ahead: int = 7) -> Dict[str, Any]:
        """List upcoming appointments in the next N days"""
        try:
            if not self.service:
                raise Exception("Calendar service not initialized")

            # Calculate time range
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'

            # Get events
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            appointments = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                appointments.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No title'),
                    'start': start,
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                })

            return {
                'success': True,
                'appointments': appointments,
                'count': len(appointments)
            }

        except Exception as e:
            logger.error(f"Failed to list appointments: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_calendar_info(self) -> Dict[str, Any]:
        """Get calendar information"""
        try:
            if not self.service:
                raise Exception("Calendar service not initialized")

            calendar = self.service.calendars().get(calendarId=self.calendar_id).execute()
            return {
                'success': True,
                'calendar_name': calendar.get('summary', 'Primary Calendar'),
                'calendar_id': calendar.get('id', ''),
                'timezone': calendar.get('timeZone', ''),
                'description': calendar.get('description', '')
            }

        except Exception as e:
            logger.error(f"Failed to get calendar info: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Global Calendar service instance
_calendar_service = None

def get_calendar_service() -> CalendarService:
    """Get a singleton Calendar service instance"""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService()
    return _calendar_service

def create_appointment_quick(patient_name: str, patient_email: str,
                           appointment_date: str, appointment_time: str,
                           doctor_name: str, department: str) -> Dict[str, Any]:
    """Quick function to create an appointment"""
    try:
        service = get_calendar_service()
        return service.create_appointment_event(
            patient_name=patient_name,
            patient_email=patient_email,
            patient_phone="Not provided",  # Default if not available
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            doctor_name=doctor_name,
            department=department
        )
    except Exception as e:
        logger.error(f"Quick create appointment failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

# Test function
if __name__ == "__main__":
    # Test the calendar service
    service = CalendarService()

    # Test calendar info
    info = service.get_calendar_info()
    print(f"Calendar info: {info}")

    # Test creating an appointment
    result = service.create_appointment_event(
        patient_name="Test Patient",
        patient_email="lalithkishore@gmail.com",
        patient_phone="123-456-7890",
        appointment_date="2024-12-25",
        appointment_time="10:00 AM",
        doctor_name="Dr. Test",
        department="Testing"
    )
    print(f"Create appointment result: {result}")