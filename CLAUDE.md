# Pipecat Voice Agent Project

## Overview
**Enterprise-grade voice agent for Renova Hospitals** with React frontend and Python backend using Pipecat AI + Gemini Live for real-time speech-to-speech conversations. Features multi-language support (English/Hindi/Telugu), advanced appointment management with calendar integration, comprehensive Google Services integration, and persistent data storage with analytics.

**Key Capabilities**: 4 voice options, 24kHz audio, Twilio phone integration, real-time calendar availability checking, automated email confirmations, appointment cancellation, patient data management, dual storage (CSV + Google Sheets), and mandatory call logging with analytics.

## Features

### Core Voice Agent
✅ **Gemini Live Pipeline**: Single API for STT+LLM+TTS (lower latency than multi-service)
✅ **Voice Selection**: 4 voices (Puck, Charon, Kore, Fenrir) with 24kHz natural audio
✅ **Multi-Language Support**: English, Hindi, Telugu with native pronunciation
✅ **Twilio Integration**: Phone calls with auto hang-up and mulaw conversion
✅ **Cross-Platform**: Windows/macOS/Linux with proper signal handling

### Enhanced Appointment System
✅ **Calendar Availability Checking**: Real-time conflict detection with alternative suggestions
✅ **Advanced Appointment Booking**: Email + Calendar integration with confirmation
✅ **Appointment Cancellation**: Verification-based cancellation with calendar cleanup
✅ **Patient Information Management**: Persistent storage and retrieval
✅ **Business Process Flow**: Proper step-by-step appointment booking with availability validation

### Google Services Integration (Complete Suite)
✅ **Gmail API**: Automated appointment confirmation emails
✅ **Calendar API**: Real-time scheduling and availability checking
✅ **Google Sheets**: Persistent data storage for call logs and patient records
✅ **Google Drive**: Organized folder structure for data management
✅ **Single OAuth Token**: Unified authentication across all Google services

### Data Management & Analytics
✅ **Dual Storage System**: CSV (local) + Google Sheets (cloud) for redundancy
✅ **Mandatory Call Logging**: Automatic logging at end of every call (silent)
✅ **Patient Database**: Comprehensive patient record management
✅ **Call Analytics**: Duration, language, resolution tracking
✅ **Multi-Language Call Handling**: Automatic language detection and response
✅ **Customer Detection**: Automatic identification of new/existing/returning customers
✅ **Session-Aware Function Calling**: Real-time call record updates during conversations

## Project Structure
```
MyVoiceAgent/
├── frontend/                 # React frontend application
│   ├── public/
│   │   ├── index.html        # HTML template with PWA support
│   │   └── manifest.json     # Web app manifest
│   ├── src/
│   │   ├── hooks/
│   │   │   └── useWebRTCClient.js  # WebRTC hook replacing Daily.co
│   │   ├── components/
│   │   │   └── VoiceChat.jsx       # Main voice chat component
│   │   ├── App.js            # Main app component
│   │   ├── App.css           # Professional styling
│   │   ├── index.js          # React entry point
│   │   └── index.css         # Global styles
│   ├── package.json          # React dependencies
│   └── .env                  # Frontend configuration
└── server/                   # Python backend server
    ├── src/
    │   ├── pipecat_server.py # PRODUCTION: Enhanced Gemini Live with full Google integration (PORT 8090)
    │   ├── enhanced_appointment_functions.py # Complete appointment system with availability, booking, cancellation
    │   ├── gmail_service.py  # Gmail API service for sending emails
    │   ├── calendar_service.py # Google Calendar API service with availability checking
    │   ├── google_sheets_service.py # Google Sheets API for call logs and patient data
    │   ├── call_logger.py    # CSV-based call logging system
    │   ├── gmail_routes.py   # FastAPI routes for Gmail functionality
    │   ├── googel_auth_manger.py # Google OAuth2 authentication manager (all Google APIs)
    │   ├── test_sheets_setup.py # Google Sheets integration testing script
    │   ├── test_google_drive.py # Google Drive API testing script
    │   ├── twilio_pipecat_integrated.py # TWILIO: Phone integration server (PORT 8091)
    │   ├── audio_bridge.py   # Twilio audio format bridge (mulaw ↔ PCM)
    │   ├── main.py           # Original complex server (deprecated)
    │   ├── simple_server.py  # Working simplified Pipecat server
    │   ├── windows_server.py # Windows-compatible server version
    │   ├── session_manager.py # Global session management (up to 50 sessions)
    │   ├── voice_session.py   # Individual voice session with Gemini Live
    │   └── websocket_handler.py # WebSocket message handling & routing
    ├── requirements.txt      # Original dependencies
    ├── requirements-pipecat.txt # Working Pipecat dependencies
    ├── requirements-simple.txt # Simplified installation
    ├── requirements-minimal.txt # Minimal dependencies
    ├── Dockerfile           # Multi-stage production deployment
    ├── setup.py             # Automated setup script
    ├── install.bat          # Windows installation script
    ├── install.sh           # macOS/Linux installation script
    ├── .env                 # Server configuration with Gemini API key
    └── .env.example         # Configuration template
```

## Tech Stack
**Frontend**: React 18.2.0 + Pipecat SDK + ProtobufFrameSerializer
**Backend**: Python 3.8+ + FastAPI + GeminiMultimodalLiveLLMService
**Audio**: 24kHz output (critical for natural voice), 16kHz input, SileroVAD
**Integration**: Gmail API + Calendar API + Twilio Voice + TwilioFrameSerializer

## Endpoints
**Web (8090)**: `ws://localhost:8090/ws?voice_id=Charon` | `GET /health`
**Phone (8091)**: `POST /` (Twilio webhook) | `wss://ngrok-url/ws` (Media Stream)
**Available Voices**: Puck, Charon, Kore, Fenrir

## Enhanced API Endpoints

### Core Endpoints
- **GET /** - Server info with active sessions count
- **GET /health** - Health check with detailed status including Google Sheets integration
- **WebSocket /ws?voice_id=Charon** - Voice chat with selected voice

### Data Endpoints
- **GET /call-logs** - Recent call logs from both CSV and Google Sheets
- **GET /patients** - Patient database from local memory
- **GET /patient/{phone}** - Specific patient information
- **GET /gmail/test** - Gmail API connection test

### Function Calling Capabilities (Voice-Triggered)
- **check_appointment_availability(date, time)** - Real-time calendar conflict checking
- **book_appointment(name, email, phone, date, time, doctor, department)** - Complete booking with email + calendar
- **cancel_appointment(name, email, phone, date, time, doctor)** - Verified cancellation with cleanup
- **log_call_information()** - Manual call logging (automatic at session end)

## Google Sheets Integration

### Required Structure
**VoiceAgent** folder in Google Drive containing:

**PatientData** spreadsheet ("Patients" sheet):
```
Phone | Name | Email | Last_Visit | Preferred_Doctor | Department | Language | Customer_Type | Notes | Created | Updated
```

**CallLog** spreadsheet ("Calls" sheet):
```
Call_ID | Timestamp | Phone | Name | Duration_Seconds | Language | Call_Type | Department | Doctor | Status | Resolution | Notes
```

### Data Flow
1. **Patient Data**: Voice agent stores patient info in both local memory (session) and Google Sheets (persistent)
2. **Call Logging**: Every call automatically logged to both CSV (local backup) and Google Sheets (cloud storage)
3. **Analytics**: Call duration, language usage, resolution status tracking
4. **Retrieval**: Patient history available for returning customers

## Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Twilio (Phone Calls)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
NGROK_URL=https://your-ngrok-url.ngrok-free.app

# Server
HOST=0.0.0.0
PORT=8091
MAX_SESSIONS=50
SESSION_TIMEOUT=1800
```

## Quick Start
```bash
# Frontend
cd frontend && npm install && npm start  # → http://localhost:3000

# Backend
cd server && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with GEMINI_API_KEY

# Run Servers
python src/pipecat_server.py      # Web interface (port 8090)
python src/twilio_pipecat_integrated.py  # Phone integration (port 8091)
```

## Testing & Verification

### Google Services Setup Test
```bash
cd server/src
python test_google_drive.py    # Verify Drive/Sheets API access
python test_sheets_setup.py    # Test Google Sheets integration with sample data
```

### API Endpoint Testing
```bash
# Health check
curl http://localhost:8090/health

# Call logs (both CSV and Google Sheets)
curl http://localhost:8090/call-logs

# Patient database
curl http://localhost:8090/patients

# Gmail API test
curl http://localhost:8090/gmail/test
```

### Voice Agent Testing Scenarios

**Basic Appointment Booking**:
1. "Hi, I need to book an appointment"
2. Provide: Name, phone, email, preferred date/time
3. Verify: Email sent + Calendar event created + Data logged

**Availability Checking**:
1. "I want an appointment for today at 2 PM"
2. System checks calendar conflicts
3. Suggests alternatives if busy

**Appointment Cancellation**:
1. "I need to cancel my appointment"
2. Provide: Name, date, time, doctor
3. Verify: Calendar event removed

**Multi-Language Support**:
1. Speak in Hindi/Telugu
2. Verify: Bot responds in same language
3. Check: Function parameters still in English

**Call Logging Verification**:
1. Complete any call interaction
2. Check: CSV file updated (`server/call_logs.csv`)
3. Check: Google Sheets CallLog updated
4. Verify: Patient data in Google Sheets PatientData

## WebSocket Protocol
**Client**: `start-session`, `offer`, `answer`, `ice-candidate`, `end-session`, `ping`
**Server**: `session-created`, `answer`, `session-ended`, `error`, `pong`

## Architecture
**Frontend**: useWebRTCClient → VoiceChat → WebSocket + WebRTC
**Backend**: FastAPI → Session Manager → Gemini Live → Audio Pipeline
**Pipeline**: `Audio → Gemini Live (STT+LLM+TTS) → Audio` (single service, lower latency)

## 📧 Function Calling & Appointment Booking

Voice agent uses Gemini Live function calling for appointment booking with automatic email + calendar creation.

**Flow**: Patient speaks → AI collects details → Calls `send_appointment_email()` → Gmail API sends confirmation

**Files**: `appointment_functions.py` (schemas), `gmail_service.py` (API), `pipecat_server.py` (integration)

**Key**: ✅ Use function calling (NOT text interception) - only method that works with Gemini Live

## 🎯 Function Calling Pattern (Critical!)

**⚠️ ALWAYS use Function Calling - NEVER text interception with Gemini Live!**

**Why**: Gemini Live = audio-to-audio pipeline, no TextFrames emitted

```python
# 1. Define schema + tools
function_schema = FunctionSchema(name="your_function", properties={...})
tools = ToolsSchema(standard_tools=[function_schema])

# 2. Configure LLM with tools
llm = GeminiMultimodalLiveLLMService(tools=tools)
llm.register_function("your_function", handle_your_function)

# 3. CRITICAL: Add context aggregation (required!)
context = OpenAILLMContext(tools=tools)
context_aggregator = llm.create_context_aggregator(context)

# 4. Pipeline with aggregators
pipeline = Pipeline([
    transport.input(),
    context_aggregator.user(),      # REQUIRED
    llm,
    transport.output(),
    context_aggregator.assistant()  # REQUIRED
])
```

**Must Have**: tools param + function registration + context aggregators + consistent system instructions

## 🔄 Business Process Flow (Critical!)

**Proper Appointment Booking Process:**

```
Customer Call → Data Collection → Availability Check → Booking Confirmation
```

**Step-by-Step Implementation:**

1. **Customer Contact**: Patient calls or connects via web interface
2. **Information Gathering**:
   - Patient name
   - Phone number (triggers automatic customer detection)
   - Email address
   - Appointment preferences (date, time, department, doctor)

3. **Customer Detection Logic**:
   ```python
   # Check local session memory first
   if phone in patient_database:
       customer_type = "existing"
   # Then check Google Sheets for historical data
   elif global_sheets_service.get_patient_by_phone(phone):
       customer_type = "returning"
   else:
       customer_type = "new"
   ```

4. **CRITICAL: Two-Step Booking Process**:
   ```
   Step 1: check_appointment_availability(date, time)
   ├── Available: Proceed to Step 2
   └── Not Available: Present alternatives, repeat check

   Step 2: book_appointment(patient_data)
   ├── Double-check availability (safety measure)
   ├── Send email confirmation (Gmail API)
   ├── Add to hospital calendar (Calendar API)
   └── Log complete call record (Google Sheets)
   ```

**Why Two-Step Process?**
- Prevents double-booking conflicts
- Provides real-time availability checking
- Allows graceful handling of scheduling conflicts
- Ensures data consistency across systems

**Function Call Sequence:**
```python
# CORRECT sequence
1. check_appointment_availability()  # Verify slot is free
2. book_appointment()               # Complete booking process

# INCORRECT (old method)
1. send_appointment_email()         # Direct booking without check
```

## 📞 Twilio Phone Integration

**Setup**:
1. `ngrok http 8091` → Copy HTTPS URL
2. Add Twilio vars to `.env` (SID, TOKEN, PHONE, NGROK_URL)
3. `python src/twilio_pipecat_integrated.py`
4. Twilio Console: Set webhook to `https://ngrok-url/`

**Flow**: Call → Webhook → TwiML → Media Stream → TwilioFrameSerializer → Gemini Live

**Files**: `twilio_pipecat_integrated.py` (main), `audio_bridge.py` (mulaw conversion)

**Debug**:
- "Application Error" → Check webhook URL has `/`
- No audio → Verify TwilioFrameSerializer has stream_sid + call_sid
- `curl -X POST https://ngrok-url/` to test webhook

## Troubleshooting

**Voice Quality**:
- Robotic voice → Use `audio_out_sample_rate=24000` (CRITICAL!)
- No greeting → Queue `LLMRunFrame()` on connection
- Poor audio → Use ProtobufFrameSerializer (not JSON)

**Connection**:
- DecodeError → Use official Pipecat SDK
- Voice selection → Check URL param `?voice_id=Charon`
- Windows issues → `PipelineRunner(handle_sigint=False)`

**Debug**: `curl http://localhost:8090/health` | Check logs with `python src/pipecat_server.py`

## 🎯 Critical Best Practices

**Audio Quality** (Most Important!):
```python
# ✅ CORRECT: 24kHz output for natural voice (fixes robotic speech!)
audio_out_sample_rate=24000, audio_in_sample_rate=16000

# ✅ CORRECT: Voice selection
llm = GeminiMultimodalLiveLLMService(voice_id="Charon")  # Puck/Charon/Kore/Fenrir

# ✅ CORRECT: Transport
FastAPIWebsocketTransport(params=FastAPIWebsocketParams(
    vad_analyzer=SileroVADAnalyzer(),
    serializer=ProtobufFrameSerializer(),
    audio_out_sample_rate=24000  # CRITICAL
))

# ✅ CORRECT: Windows compatibility
runner = PipelineRunner(handle_sigint=False)
```

**Date Context for Appointments**:
```python
system_instruction=f"""
Today's date: {datetime.now().strftime('%Y-%m-%d')}
"tomorrow" = {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
ALWAYS convert relative dates to YYYY-MM-DD format for functions.
"""
```

**Function Calling (ONLY method for external actions)**:
- ✅ DO: Use function schemas + tools + context aggregators
- ❌ DON'T: Text interception (doesn't work with Gemini Live audio pipeline)

## Production Deployment
**Docker**: Multi-stage builds, health checks, non-root user
**Config**: Production API keys, CORS, metrics, session limits
**Monitoring**: `/health` endpoint, JSON logs, auto cleanup

## 🔐 OAuth2 Authentication

**Critical Issue**: Single token with ALL scopes needed in BOTH locations

```bash
# Setup
cp credentials.json server/gclientsec.json.json
cd server/src && python gmail_service.py  # Triggers OAuth
cp google_token.pickle ../google_token.pickle  # Copy to both locations

# Required scopes
SCOPES = [
    'gmail.send', 'gmail.readonly',  # Email
    'calendar', 'calendar.events'    # Calendar
]
```

**Common Problem**: Voice agent runs from `server/` but token only in `server/src/`
**Solution**: Keep identical complete tokens in both `server/` and `server/src/`

**Fix Auth Errors**:
```bash
# Delete all tokens and recreate fresh
rm server/google_token.pickle server/src/google_token.pickle
cd server/src && python -c "from googel_auth_manger import get_credentials; get_credentials()"
cp google_token.pickle ../google_token.pickle
```

## 🌐 Google Services Integration

**Adding New Services (Drive, Sheets, etc.)**:
1. Plan ALL scopes upfront (adding later breaks tokens)
2. Update `googel_auth_manger.py` with new scopes
3. Delete all tokens: `rm server/google_token.pickle server/src/google_token.pickle`
4. Recreate fresh token with all scopes
5. Test all services before deployment

**Pattern for All Google Services**:
```python
# Standard service pattern
class NewGoogleService:
    def __init__(self):
        creds = get_credentials()  # Central auth manager
        self.service = build('servicename', 'version', credentials=creds)

    def test_connection(self):
        # Always include test method
        return {'success': True/False}
```

**Critical Rules**:
- ❌ Never create separate tokens for different services
- ❌ Never add scopes to existing tokens
- ✅ Always specify timezone in Calendar events
- ✅ Always use comprehensive error handling

## Future Enhancements
**Planned**: JWT auth, rate limiting, database integration, load balancing, metrics dashboard
**Scalability**: Multi-instance deployment, Redis sessions, conversation logging, multi-language

## Coding Guidelines

**CRITICAL: Windows Unicode/Encoding Rules**:
- NEVER use Unicode characters (emojis, checkmarks, crosses) in Python code or print statements
- Windows cmd/console has encoding issues with Unicode characters like ✅ ❌ 🎉
- Always use plain text: "SUCCESS:", "ERROR:", "WARNING:" instead of emoji symbols
- This prevents UnicodeEncodeError crashes that waste time debugging

**Function Call Architecture (Pipecat + Gemini Live)**:
- ALWAYS use async function handlers with FunctionCallParams: `async def handler(params: FunctionCallParams)`
- NEVER use sync wrappers for async handlers - causes "takes 1 argument but 6 were given" errors
- ALWAYS register with: `llm.register_function(name, async_handler)`
- Function calling is the ONLY way to trigger external actions - text interception doesn't work

**Data Type Consistency**:
- CallLogger.log_call() expects Dict, not CallRecord object - convert before calling
- Always check expected input types for existing functions before calling
- Use dataclasses for structured data, dicts for legacy interfaces

**Google Services Integration**:
- ALWAYS use single shared credentials across all Google services (Gmail/Calendar/Sheets)
- NEVER create separate tokens - breaks OAuth scope management
- Use absolute paths for credential files, not relative paths
- Always test sheet structure exists before writing data

**Error Handling Patterns**:
```python
# CORRECT: Non-blocking error handling
try:
    result = some_operation()
    logger.info("SUCCESS: Operation completed")
except Exception as e:
    logger.error(f"ERROR: Operation failed: {e}")
    # Continue execution, don't crash entire session
```

**Server Management**:
- NEVER start servers automatically in code - always ask user first
- User controls when to start/stop servers to see logs
- Close background servers when done testing

**Path Handling**:
- Use pathlib for cross-platform paths: `Path(__file__).parent.parent`
- Avoid hardcoded relative paths like "../../file.json"
- Always verify file existence before operations

**Frontend Integration**:
- Backend changes shouldn't break frontend connections
- Test /health endpoint after backend changes
- Keep consistent port configurations (8090 for web, 8091 for Twilio)

**Example**:
```python
# WRONG - causes Windows encoding errors
print("✅ Success!")
print("❌ Failed!")

# CORRECT - works on all platforms
print("SUCCESS: Operation completed!")
print("ERROR: Operation failed!")
```

## Recent Enhancements & Fixes

### Business Process Flow Implementation ✅
- **Fixed availability confirmation conflict**: Implemented proper two-step booking process
- **Enhanced system instructions**: Clear function calling sequence (check availability → book appointment)
- **Session-aware function calling**: Real-time call record updates during conversations
- **Customer detection logic**: Multi-tier identification (local memory → Google Sheets → new customer)

### Critical Function Call Pattern ✅
```python
# CORRECT Implementation (Fixed)
1. check_appointment_availability(date, time)  # Verify slot availability
2. book_appointment(patient_data)             # Complete booking process

# Previous Issue (Resolved)
Direct booking without availability checking caused conflicts
```

### Data Management Improvements ✅
- **Complete call logging**: All patient information now captured during conversations
- **Dual storage redundancy**: CSV + Google Sheets for data persistence
- **Automatic customer recognition**: Personalized experience for returning patients
- **Real-time session tracking**: Live updates to call records as conversation progresses

### System Stability ✅
- **Enhanced error handling**: Graceful fallbacks for all function calls
- **Consistent system instructions**: Aligned with enhanced function capabilities
- **Proper OAuth scoping**: Single token for all Google services
- **Windows compatibility**: Signal handling and path resolution fixes

## Credits
**Tech Stack**: Pipecat AI + Gemini Live + React + FastAPI + WebRTC
**APIs**: Gemini Live (pay-per-use), Gmail, Calendar, Twilio Voice