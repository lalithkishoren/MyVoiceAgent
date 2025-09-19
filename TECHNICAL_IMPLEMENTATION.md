# Renova Hospitals Voice Agent - Technical Implementation Documentation

## Overview

This document provides detailed technical implementation details for the Renova Hospitals Voice Agent system, including architecture, APIs, function implementations, data flows, and integration patterns.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Function Call Implementation](#function-call-implementation)
3. [Data Flow Architecture](#data-flow-architecture)
4. [API Integrations](#api-integrations)
5. [Session Management](#session-management)
6. [Error Handling Patterns](#error-handling-patterns)
7. [Performance Optimization](#performance-optimization)
8. [Deployment & DevOps](#deployment--devops)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │  External APIs  │
│   React App     │◄──►│   FastAPI       │◄──►│  Google Services│
│   Port 3000     │    │   Port 8090     │    │  Gmail/Calendar │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Twilio        │
                       │   Phone System  │
                       │   Port 8091     │
                       └─────────────────┘
```

### Core Components

#### 1. FastAPI Server (`pipecat_server.py`)
- **Primary Server**: Handles web interface connections
- **WebSocket Protocol**: Real-time voice communication
- **Session Management**: Multi-user session handling
- **Function Registration**: Enhanced appointment functions

#### 2. Gemini Live Integration
- **LLM Service**: `GeminiMultimodalLiveLLMService`
- **Voice Processing**: Real-time STT + LLM + TTS
- **Function Calling**: Advanced appointment management
- **Context Management**: Conversation state maintenance

#### 3. Enhanced Function System
- **Availability Checking**: Real-time calendar integration
- **Appointment Booking**: Multi-step verification process
- **Call Logging**: Comprehensive data capture
- **Customer Detection**: Multi-tier identification

---

## Function Call Implementation

### Core Function Architecture

#### Function Registry Pattern
```python
# Enhanced function registry
ENHANCED_FUNCTION_REGISTRY = {
    "check_appointment_availability": handle_check_appointment_availability,
    "book_appointment": handle_book_appointment,
    "cancel_appointment": handle_cancel_appointment,
    "log_call_information": handle_log_call_information
}

# Session-aware wrapper
def create_session_aware_handler(original_handler, func_name):
    async def wrapped_handler(params):
        # Add session context
        params.arguments['session_id'] = session_id

        # Execute function
        result = await original_handler(params)

        # Update call records
        update_call_record(session_id, params.arguments)

        return result
    return wrapped_handler
```

### 1. Appointment Availability Checking

#### Function Schema
```python
check_availability_schema = FunctionSchema(
    name="check_appointment_availability",
    description="Check if appointment slot is available",
    properties={
        "appointment_date": {
            "type": "string",
            "description": "Date in YYYY-MM-DD format"
        },
        "appointment_time": {
            "type": "string",
            "description": "Time in HH:MM AM/PM format"
        },
        "duration_minutes": {
            "type": "integer",
            "description": "Duration in minutes (default 30)"
        }
    },
    required=["appointment_date", "appointment_time"]
)
```

#### Implementation Flow
```python
async def handle_check_appointment_availability(params: FunctionCallParams):
    # 1. Extract parameters
    date = params.arguments.get("appointment_date")
    time = params.arguments.get("appointment_time")
    duration = params.arguments.get("duration_minutes", 30)

    # 2. Calendar service integration
    calendar_service = get_calendar_service()
    availability_result = calendar_service.check_availability(
        appointment_date=date,
        appointment_time=time,
        duration_minutes=duration
    )

    # 3. Process results
    if availability_result.get('available'):
        await params.result_callback({
            "success": True,
            "available": True,
            "message": "Time slot is available",
            "requested_slot": availability_result.get('requested_slot')
        })
    else:
        # Generate alternatives
        alternatives = availability_result.get('alternatives', [])
        await params.result_callback({
            "success": True,
            "available": False,
            "message": "Time slot not available",
            "alternatives": alternatives
        })
```

### 2. Appointment Booking Process

#### Function Schema
```python
book_appointment_schema = FunctionSchema(
    name="book_appointment",
    description="Book appointment with confirmation",
    properties={
        "patient_name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
        "appointment_date": {"type": "string"},
        "appointment_time": {"type": "string"},
        "doctor_name": {"type": "string"},
        "department": {"type": "string"}
    },
    required=["patient_name", "email", "appointment_date",
             "appointment_time", "doctor_name", "department"]
)
```

#### Implementation with Safety Checks
```python
async def handle_book_appointment(params: FunctionCallParams):
    # 1. Extract and validate data
    patient_data = extract_patient_data(params.arguments)

    # 2. CRITICAL: Double-check availability
    calendar_service = get_calendar_service()
    availability_check = calendar_service.check_availability(
        appointment_date=patient_data['date'],
        appointment_time=patient_data['time']
    )

    if not availability_check.get('available', True):
        # Slot no longer available
        await params.result_callback({
            "success": False,
            "available": False,
            "message": "Time slot no longer available",
            "alternatives": availability_check.get('alternatives', [])
        })
        return

    # 3. Execute booking process
    # Email confirmation
    gmail_service = get_gmail_service()
    email_result = send_confirmation_email(patient_data)

    # Calendar integration
    calendar_result = create_calendar_event(patient_data)

    # Call logging
    log_call_record(patient_data)

    # 4. Return comprehensive result
    await params.result_callback({
        "success": True,
        "message": "Appointment confirmed",
        "email_sent": email_result.get('success'),
        "calendar_added": calendar_result.get('success'),
        "appointment_details": patient_data
    })
```

---

## Data Flow Architecture

### Real-Time Data Synchronization

#### 1. Session-Level Data Flow
```
User Input → Function Call → Data Update → Multiple Storage Points
                    ↓
            ┌─────────────────┐
            │ Session Memory  │ (Immediate access)
            └─────────────────┘
                    ↓
            ┌─────────────────┐
            │ Call Records    │ (Real-time tracking)
            └─────────────────┘
                    ↓
            ┌─────────────────┐
            │ Google Sheets   │ (Persistent storage)
            └─────────────────┘
                    ↓
            ┌─────────────────┐
            │ Local CSV       │ (Backup storage)
            └─────────────────┘
```

#### 2. Customer Detection Data Flow
```python
def detect_customer_type(phone_number):
    # Level 1: Current session memory
    if phone_number in patient_database:
        return "existing", patient_database[phone_number]

    # Level 2: Google Sheets historical data
    if global_sheets_service:
        patient_record = global_sheets_service.get_patient_by_phone(phone_number)
        if patient_record:
            # Cache in session memory
            patient_database[phone_number] = convert_to_dict(patient_record)
            return "returning", patient_database[phone_number]

    # Level 3: New customer
    return "new", None
```

### Call Record Lifecycle

#### Creation and Updates
```python
class CallRecord:
    def __init__(self, session_id, caller_phone=None):
        self.call_id = str(uuid.uuid4())
        self.session_id = session_id
        self.timestamp = datetime.now()
        self.caller_phone = caller_phone
        self.customer_name = ""
        self.customer_email = ""
        self.language = "english"
        self.call_type = "inquiry"
        self.status = "in_progress"

    def update_from_function_call(self, function_name, arguments):
        """Update record based on function call data"""
        if function_name in ['book_appointment', 'check_appointment_availability']:
            self.customer_name = arguments.get('patient_name', self.customer_name)
            self.customer_email = arguments.get('email', self.customer_email)
            self.department_enquired = arguments.get('department', '')
            self.doctor_enquired = arguments.get('doctor_name', '')
            self.call_type = "appointment_booking"
```

---

## API Integrations

### Google Services Integration

#### 1. Gmail API Implementation
```python
class GmailService:
    def __init__(self):
        self.credentials = get_credentials()
        self.service = build('gmail', 'v1', credentials=self.credentials)

    def send_appointment_confirmation(self, patient_data):
        # Create HTML email content
        subject, body = create_appointment_email_html(patient_data)

        # Create message
        message = MIMEMultipart()
        message['to'] = patient_data['email']
        message['subject'] = subject

        # Add HTML body
        html_part = MIMEText(body, 'html')
        message.attach(html_part)

        # Send via Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            return {
                'success': True,
                'message_id': result['id']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

#### 2. Calendar API Implementation
```python
class CalendarService:
    def __init__(self):
        self.credentials = get_credentials()
        self.service = build('calendar', 'v3', credentials=self.credentials)
        self.calendar_id = 'primary'

    def check_availability(self, appointment_date, appointment_time, duration=30):
        # Parse datetime
        start_datetime = self._parse_appointment_datetime(appointment_date, appointment_time)
        end_datetime = start_datetime + timedelta(minutes=duration)

        # Query existing events
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=start_datetime.isoformat() + '+05:30',
            timeMax=end_datetime.isoformat() + '+05:30',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Check for conflicts
        conflicts = self._check_time_conflicts(events, start_datetime, end_datetime)

        if not conflicts:
            return {
                'success': True,
                'available': True,
                'message': 'Time slot is available'
            }
        else:
            alternatives = self._suggest_alternative_slots(start_datetime, conflicts)
            return {
                'success': True,
                'available': False,
                'conflicts': conflicts,
                'alternatives': alternatives
            }
```

#### 3. Google Sheets Implementation
```python
class GoogleSheetsService:
    def __init__(self, credentials=None):
        self.credentials = credentials or get_credentials()
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials)

        # Initialize sheet IDs
        self.patient_sheet_id = self._get_or_create_patient_sheet()
        self.calllog_sheet_id = self._get_or_create_calllog_sheet()

    def save_patient_data(self, patient_record):
        """Save patient data to Google Sheets"""
        values = [
            patient_record.phone,
            patient_record.name,
            patient_record.email,
            patient_record.last_visit,
            patient_record.preferred_doctor,
            patient_record.department,
            patient_record.language,
            patient_record.customer_type,
            patient_record.notes,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]

        body = {
            'values': [values]
        }

        try:
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.patient_sheet_id,
                range='Patients!A:K',
                valueInputOption='RAW',
                body=body
            ).execute()

            return {'success': True, 'updated_cells': result.get('updates', {})}
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

---

## Session Management

### Multi-Session Architecture

#### Session Storage
```python
# Global session management
active_sessions = {}  # {session_id: session_data}
session_call_records = {}  # {session_id: CallRecord}
patient_database = {}  # {phone: patient_info} - session memory

class SessionManager:
    def __init__(self):
        self.max_sessions = 50
        self.session_timeout = 1800  # 30 minutes

    def create_session(self, websocket, voice_id="Charon"):
        session_id = str(uuid.uuid4())

        session_data = {
            'id': session_id,
            'websocket': websocket,
            'voice_id': voice_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'status': 'active'
        }

        # Initialize call record
        call_record = CallRecord(session_id)

        # Store in global state
        active_sessions[session_id] = session_data
        session_call_records[session_id] = call_record

        return session_id

    def cleanup_session(self, session_id):
        """Clean up session and finalize call record"""
        if session_id in session_call_records:
            call_record = session_call_records[session_id]

            # Calculate final duration
            if call_record.start_time:
                duration = (datetime.now() - call_record.start_time).total_seconds()
                call_record.duration_seconds = int(duration)

            # Save final call record
            self._save_call_record(call_record)

            # Cleanup memory
            del session_call_records[session_id]

        if session_id in active_sessions:
            del active_sessions[session_id]
```

### Real-Time Session Updates

#### Function Call Integration
```python
def update_call_record_from_function(session_id, function_name, arguments):
    """Update call record when functions are called"""
    if session_id not in session_call_records:
        return

    call_record = session_call_records[session_id]

    # Update based on function type
    if function_name in ['book_appointment', 'send_appointment_email']:
        # Extract patient information
        phone = arguments.get('phone')
        patient_name = arguments.get('patient_name')
        email = arguments.get('email')

        # Customer detection
        customer_type = detect_customer_type(phone)

        # Update call record
        call_record.customer_name = patient_name or call_record.customer_name
        call_record.customer_email = email or call_record.customer_email
        call_record.caller_phone = phone or call_record.caller_phone
        call_record.customer_type = customer_type
        call_record.call_type = "appointment_booking"

        # Update department and doctor if provided
        if arguments.get('department'):
            call_record.department_enquired = arguments['department']
        if arguments.get('doctor_name'):
            call_record.doctor_enquired = arguments['doctor_name']
```

---

## Error Handling Patterns

### Graceful Degradation Strategy

#### 1. API Failure Handling
```python
async def robust_function_execution(func, *args, **kwargs):
    """Execute function with multiple fallback strategies"""
    try:
        # Primary execution
        return await func(*args, **kwargs)
    except GoogleAPIException as e:
        # Google service failure - use local storage
        logger.warning(f"Google API failure: {e}")
        return await fallback_to_local_storage(*args, **kwargs)
    except NetworkException as e:
        # Network failure - queue for retry
        logger.error(f"Network failure: {e}")
        return await queue_for_retry(*args, **kwargs)
    except Exception as e:
        # Unknown failure - log and provide user feedback
        logger.error(f"Unexpected error: {e}")
        return await provide_error_feedback(*args, **kwargs)
```

#### 2. Function Call Error Recovery
```python
async def safe_function_call_handler(original_handler):
    """Wrapper for safe function execution"""
    async def wrapper(params):
        try:
            result = await original_handler(params)

            # Success callback
            await params.result_callback({
                "success": True,
                "result": result
            })

        except ValidationError as e:
            # Parameter validation failed
            await params.result_callback({
                "success": False,
                "error_type": "validation",
                "message": "Please provide valid information",
                "details": str(e)
            })

        except ExternalServiceError as e:
            # External service failed
            await params.result_callback({
                "success": False,
                "error_type": "service",
                "message": "Service temporarily unavailable, please try again",
                "details": str(e)
            })

        except Exception as e:
            # Unknown error
            logger.error(f"Function call error: {e}")
            await params.result_callback({
                "success": False,
                "error_type": "unknown",
                "message": "An unexpected error occurred"
            })

    return wrapper
```

---

## Performance Optimization

### Caching Strategies

#### 1. Patient Data Caching
```python
class PatientDataCache:
    def __init__(self, ttl=3600):  # 1 hour TTL
        self.cache = {}
        self.ttl = ttl

    def get_patient(self, phone_number):
        """Get patient with cache check"""
        cache_key = f"patient_{phone_number}"

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                return cached_data
            else:
                del self.cache[cache_key]

        # Cache miss - fetch from Google Sheets
        patient_data = fetch_from_sheets(phone_number)

        if patient_data:
            self.cache[cache_key] = (patient_data, time.time())

        return patient_data
```

#### 2. Calendar Availability Caching
```python
class AvailabilityCache:
    def __init__(self, ttl=300):  # 5 minute TTL
        self.cache = {}
        self.ttl = ttl

    def check_availability(self, date, time):
        """Check availability with intelligent caching"""
        cache_key = f"availability_{date}_{time}"

        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                return cached_result

        # Fetch fresh data
        result = fetch_calendar_availability(date, time)

        # Cache only if available (busy slots change frequently)
        if result.get('available'):
            self.cache[cache_key] = (result, time.time())

        return result
```

### Database Connection Pooling

#### Efficient Resource Management
```python
class DatabaseConnectionManager:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.connection_pool = Queue(maxsize=max_connections)
        self.active_connections = 0

    async def get_connection(self):
        """Get database connection from pool"""
        if self.connection_pool.empty() and self.active_connections < self.max_connections:
            # Create new connection
            connection = await create_new_connection()
            self.active_connections += 1
            return connection
        else:
            # Wait for available connection
            return await self.connection_pool.get()

    async def return_connection(self, connection):
        """Return connection to pool"""
        if connection.is_healthy():
            await self.connection_pool.put(connection)
        else:
            # Replace unhealthy connection
            self.active_connections -= 1
            connection.close()
```

---

## Deployment & DevOps

### Docker Configuration

#### Multi-Stage Dockerfile
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim
WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy application
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY server/ ./server/
COPY BUSINESS_FUNCTIONALITY.md ./
COPY TECHNICAL_IMPLEMENTATION.md ./

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Expose ports
EXPOSE 8090 8091

# Start application
CMD ["python", "server/src/pipecat_server.py"]
```

### Environment Configuration

#### Production Environment Variables
```bash
# Core Configuration
GEMINI_API_KEY=production_api_key
HOST=0.0.0.0
PORT=8090
MAX_SESSIONS=100
SESSION_TIMEOUT=1800

# Google Services
GOOGLE_CLIENT_SECRETS_FILE=/app/credentials/google_credentials.json
GOOGLE_TOKEN_PICKLE=/app/data/google_token.pickle

# Twilio Integration
TWILIO_ACCOUNT_SID=production_account_sid
TWILIO_AUTH_TOKEN=production_auth_token
TWILIO_PHONE_NUMBER=production_phone_number
NGROK_URL=https://production-domain.com

# Monitoring & Logging
LOG_LEVEL=INFO
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Security
CORS_ORIGINS=["https://frontend.domain.com"]
API_RATE_LIMIT=100
```

### Monitoring & Logging

#### Structured Logging
```python
import structlog

logger = structlog.get_logger()

class StructuredLogger:
    def __init__(self):
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def log_function_call(self, function_name, session_id, arguments, result):
        """Log function call with structured data"""
        logger.info(
            "function_call_executed",
            function_name=function_name,
            session_id=session_id,
            arguments=arguments,
            result_success=result.get('success', False),
            timestamp=datetime.now().isoformat()
        )

    def log_session_event(self, event_type, session_id, details=None):
        """Log session-related events"""
        logger.info(
            "session_event",
            event_type=event_type,
            session_id=session_id,
            details=details or {},
            timestamp=datetime.now().isoformat()
        )
```

---

## Conclusion

This technical implementation provides a robust, scalable, and maintainable foundation for the Renova Hospitals Voice Agent system. The architecture emphasizes:

- **Reliability**: Multiple fallback mechanisms and error handling
- **Performance**: Caching strategies and connection pooling
- **Scalability**: Session management and resource optimization
- **Maintainability**: Structured logging and monitoring
- **Security**: Proper authentication and data protection

The modular design allows for easy extension and modification as business requirements evolve, while the comprehensive error handling ensures robust operation in production environments.