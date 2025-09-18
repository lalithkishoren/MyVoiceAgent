# Pipecat Voice Agent Project

## Overview
A complete voice agent application built with React frontend and Python backend, implementing Pipecat AI framework with Gemini Live for real-time speech-to-speech conversations. Features voice selection, natural interruption handling, high-quality 24kHz audio processing, and **full Twilio phone integration** for receiving and making phone calls.

## Current Status
✅ **Voice Pipeline**: Full Gemini Live speech-to-speech working
✅ **Voice Selection**: 4 natural voices (Puck, Charon, Kore, Fenrir)
✅ **Audio Quality**: 24kHz sample rate for natural voice output
✅ **Interruption Handling**: Natural conversation flow with proper interruption
✅ **Greeting System**: Automatic welcome message on connection
✅ **WebSocket Transport**: FastAPIWebsocketTransport with ProtobufFrameSerializer
✅ **Windows Compatibility**: Proper signal handling for Windows environment
✅ **Twilio Phone Integration**: Complete phone-to-AI conversation system
✅ **TwilioFrameSerializer**: Proper mulaw ↔ PCM audio format conversion
✅ **Auto Hang-up**: Automatic call termination via Twilio API
✅ **Email Integration**: Automatic appointment confirmation emails via Gmail API
✅ **Calendar Integration**: Automatic appointment scheduling in Google Calendar with timezone handling
✅ **Function Calling**: Gemini Live function calling for external actions
✅ **Appointment Booking**: Full end-to-end appointment booking with email + calendar integration
✅ **OAuth2 Authentication**: Robust Google API authentication with proper token management
✅ **Date Interpretation**: Correct handling of relative dates ("tomorrow", "next week") with current date context
✅ **Multi-Service Integration**: Single OAuth token supporting both Gmail and Calendar APIs

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
    │   ├── pipecat_server.py # PRODUCTION: Gemini Live with voice selection and email (PORT 8091)
    │   ├── appointment_functions.py # Email + Calendar function calling for appointment confirmations
    │   ├── gmail_service.py  # Gmail API service for sending emails
    │   ├── calendar_service.py # Google Calendar API service for scheduling appointments
    │   ├── gmail_routes.py   # FastAPI routes for Gmail functionality
    │   ├── googel_auth_manger.py # Google OAuth2 authentication manager (Gmail + Calendar scopes)
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

## Technology Stack

### Frontend
- **React 18.2.0** - UI framework
- **Pipecat JavaScript SDK** - Official client with ProtobufFrameSerializer
- **Voice Selection UI** - Dropdown for 4 Gemini Live voices
- **24kHz Audio Processing** - High-quality audio playback
- **Real-time Interruption** - Natural conversation flow
- **Modern CSS** - Glassmorphism design, gradient backgrounds, responsive layout

### Backend
- **Python 3.8+** - Server runtime
- **FastAPI + WebSockets** - Async web framework
- **GeminiMultimodalLiveLLMService** - Direct Gemini Live integration
- **FastAPIWebsocketTransport** - Official Pipecat transport
- **ProtobufFrameSerializer** - Efficient binary protocol
- **SileroVADAnalyzer** - Voice activity detection
- **Windows Signal Handling** - Cross-platform compatibility

## Key Features

### Voice Processing
- **Gemini Live Integration** - Single API for speech-to-text, language model, and text-to-speech
- **4 Voice Options** - Puck (energetic), Charon (authoritative), Kore (friendly), Fenrir (confident)
- **24kHz Audio Quality** - High sample rate for natural, non-robotic voice output
- **Natural Speech Instructions** - AI trained to use contractions, fillers, and emotional inflection
- **Automatic Greeting** - "Hi! How are you? I'm your AI Assistant..." on connection
- **Real-time Interruption** - Natural conversation flow with proper turn-taking

### Session Management
- **Concurrent Sessions** - Up to 50 simultaneous voice sessions
- **Session Timeout** - 30-minute automatic cleanup
- **Auto-reconnection** - Client-side reconnection with exponential backoff
- **Resource Management** - Automatic cleanup of expired sessions

### Audio Quality & Best Practices
- **24kHz Sample Rate** - **CRITICAL**: Use 24kHz output for natural voice (fixes robotic speech)
- **16kHz Input** - Standard microphone input rate for speech recognition
- **ProtobufFrameSerializer** - Efficient binary protocol for real-time audio
- **High-Quality Settings** - Enhanced audio processing with AGC, noise suppression
- **Natural Speech System Instructions** - Detailed prompts for human-like speech patterns

### Production Ready
- **Docker Support** - Multi-stage builds for development and production
- **Health Monitoring** - Health check endpoints and metrics collection
- **Error Handling** - Comprehensive error recovery and logging
- **Security** - CORS configuration, non-root Docker user, API validation

## API Endpoints

### WebSocket (Port 8090) - PRODUCTION
- `ws://localhost:8090/ws` - **Pipecat voice chat endpoint**
- `ws://localhost:8090/ws?voice_id=Charon` - **Voice selection parameter**
- **Available Voices**: Puck, Charon, Kore, Fenrir
- **Features**: Automatic greeting, 24kHz audio, natural interruption

### HTTP API (Port 8090)
- `GET /` - Server information and status
- `GET /health` - Health check with connection details

### Twilio Phone Integration (Port 8091) - PRODUCTION
- `POST /` - **Twilio webhook for incoming calls**
- `wss://your-ngrok-url/ws` - **Twilio Media Stream WebSocket**
- `GET /health` - Health check with Twilio configuration status
- `GET /twilio/calls` - Active phone calls information
- **Features**: Phone-to-AI conversations, automatic hang-up, mulaw audio conversion

### Legacy Endpoints (Port 8080)
- `ws://localhost:8080/ws` - Simple server (deprecated)
- `GET /sessions` - Active sessions information
- `GET /metrics` - Performance and usage metrics

## Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Twilio Integration (Phone Calls)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
NGROK_URL=https://your-ngrok-url.ngrok-free.app

# Server Settings
HOST=0.0.0.0
PORT=8091
LOG_LEVEL=INFO

# Session Management
MAX_SESSIONS=50
SESSION_TIMEOUT=1800
CLEANUP_INTERVAL=300

# Optional
DEBUG=false
CORS_ORIGINS=*
ENABLE_METRICS=true
```

### Frontend Configuration
```bash
# WebSocket URL for signaling server
REACT_APP_SIGNALING_URL=ws://localhost:8080/ws
```

## Installation & Setup

### Frontend Setup
```bash
cd frontend
npm install
# Installs: @pipecat-ai/client-js, @pipecat-ai/websocket-transport
npm start
# Available at http://localhost:3000
```

### Backend Setup (PRODUCTION)
```bash
cd server

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install Pipecat with required dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

### Start Server (PRODUCTION)
```bash
# RECOMMENDED: Pipecat server with voice selection
python src/pipecat_server.py
# WebSocket: ws://localhost:8090/ws
# HTTP API: http://localhost:8090

# TWILIO: Phone integration server
python src/twilio_pipecat_integrated.py
# WebSocket: wss://your-ngrok-url.ngrok-free.app/ws
# HTTP API: https://your-ngrok-url.ngrok-free.app/
# Phone webhook: POST https://your-ngrok-url.ngrok-free.app/

# Alternative: Use venv directly (if activation issues)
venv\Scripts\python.exe src\pipecat_server.py
venv\Scripts\python.exe src\twilio_pipecat_integrated.py
```

### Alternative Installation Options
```bash
# Option 1: Original dependencies (may have issues)
pip install -r requirements.txt

# Option 2: Simplified installation
pip install -r requirements-simple.txt

# Option 3: Minimal installation (without pipecat)
pip install -r requirements-minimal.txt
```

## WebSocket Protocol

### Client Messages
```json
// Start session
{
  "type": "start-session",
  "sessionId": "optional-uuid",
  "systemPrompt": "optional-custom-prompt",
  "offer": { /* WebRTC offer */ }
}

// WebRTC signaling
{
  "type": "offer",
  "offer": { /* SDP offer */ },
  "sessionId": "session-uuid"
}

{
  "type": "answer",
  "answer": { /* SDP answer */ },
  "sessionId": "session-uuid"
}

{
  "type": "ice-candidate",
  "candidate": { /* ICE candidate */ },
  "sessionId": "session-uuid"
}

// End session
{
  "type": "end-session",
  "sessionId": "session-uuid"
}

// Keep-alive
{
  "type": "ping"
}
```

### Server Responses
```json
// Session created
{
  "type": "session-created",
  "sessionId": "session-uuid",
  "timestamp": "2024-01-01T00:00:00Z"
}

// WebRTC responses
{
  "type": "answer",
  "answer": { /* SDP answer */ },
  "sessionId": "session-uuid"
}

// Session ended
{
  "type": "session-ended",
  "sessionId": "session-uuid",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Errors
{
  "type": "error",
  "message": "Error description",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Keep-alive response
{
  "type": "pong",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Architecture

### Frontend Architecture
```
useWebRTCClient Hook
├── WebSocket Connection Management
├── WebRTC Peer Connection Setup
├── SDP Offer/Answer Handling
├── ICE Candidate Processing
├── Audio Stream Management
├── Session Lifecycle Management
└── Auto-reconnection Logic

VoiceChat Component
├── UI State Management
├── Audio Controls
├── Connection Status Display
├── Error Handling
└── User Feedback
```

### Backend Architecture
```
FastAPI Server (main.py)
├── HTTP API Endpoints
├── WebSocket Server Integration
├── Health Monitoring
├── Metrics Collection
└── Graceful Shutdown

Session Manager
├── Session Creation/Deletion
├── Resource Management
├── Timeout Handling
├── Background Cleanup
└── Concurrent Session Limits

Voice Session (Gemini Live)
├── Gemini Live API Integration
├── WebRTC Transport Management
├── Audio Processing Pipeline
├── Session State Management
└── Error Recovery

WebSocket Handler
├── Message Routing
├── Client Connection Management
├── Protocol Validation
├── Error Handling
└── Session Association
```

## Voice Pipeline

### Traditional Multi-Service Pipeline (Previous)
```
Audio Input → Deepgram STT → OpenAI LLM → Cartesia TTS → Audio Output
```

### Current Gemini Live Pipeline
```
Audio Input → Gemini Live (STT + LLM + TTS) → Audio Output
```

### Benefits of Gemini Live
- **Lower Latency** - Single service handles entire pipeline
- **Better Integration** - Optimized for voice conversations
- **Simplified Architecture** - One API instead of three
- **Cost Efficiency** - Single service billing
- **Real-time Processing** - Native audio-to-audio capabilities

## Development Workflow

### Local Development
1. Start backend server: `python src/main.py`
2. Start frontend: `npm start`
3. Open browser to `http://localhost:3000`
4. Test voice conversations

### Docker Development
```bash
# Build and run server
cd server
docker build -t pipecat-voice .
docker run -p 8080:8080 -p 8081:8081 pipecat-voice

# Environment variables
docker run -p 8080:8080 -p 8081:8081 \
  -e GEMINI_API_KEY=your_key_here \
  pipecat-voice
```

## 📧 Email Integration & Function Calling

### Overview
Complete appointment booking system with automatic email confirmation using Gemini Live function calling. Patients can book appointments via voice and automatically receive professional HTML confirmation emails.

### Features
- ✅ **Gemini Live Function Calling** - AI calls external functions during conversation
- ✅ **Automatic Email Sending** - Confirmation emails sent after appointment booking
- ✅ **Gmail API Integration** - Uses existing Google OAuth2 authentication
- ✅ **Beautiful HTML Emails** - Professional appointment confirmation emails
- ✅ **Context Aggregation** - Proper function calling support with OpenAILLMContext
- ✅ **Error Handling** - Robust error handling and logging

### Function Calling Architecture

#### Email Function Schema
```python
send_appointment_email_function = FunctionSchema(
    name="send_appointment_email",
    description="Send appointment confirmation email to patient after booking is confirmed",
    properties={
        "patient_name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
        "appointment_date": {"type": "string"},
        "appointment_time": {"type": "string"},
        "doctor_name": {"type": "string"},
        "department": {"type": "string"}
    },
    required=["patient_name", "email", "appointment_date", "appointment_time", "doctor_name", "department"]
)
```

#### Pipeline Architecture
```python
# Function calling enabled pipeline
pipeline = Pipeline([
    transport.input(),              # Audio input from client
    context_aggregator.user(),      # User context aggregation
    llm,                           # Gemini Live with function calling
    transport.output(),            # Audio output to client
    context_aggregator.assistant() # Assistant context aggregation
])
```

### How It Works

1. **Patient speaks** to voice agent about booking appointment
2. **AI collects details** (name, email, phone, date, time, doctor preference)
3. **AI calls function** `send_appointment_email()` with collected parameters
4. **Function executes** and sends beautiful HTML email via Gmail API
5. **AI confirms** to patient: "Perfect! Your appointment is confirmed and I've sent you a confirmation email."

### File Structure
```
appointment_functions.py         # Function calling implementation
├── send_appointment_email_function    # Function schema definition
├── appointment_tools                  # ToolsSchema for Gemini Live
├── create_appointment_email_html()    # HTML email template generation
├── handle_send_appointment_email()    # Async function handler
└── Professional HTML email template   # Renova Hospitals branding

gmail_service.py                # Gmail API service (existing)
├── GmailService                # Main service class
├── send_simple_email()         # Email sending functionality
└── OAuth2 authentication      # Google API integration

pipecat_server.py              # Main server with function calling
├── GeminiMultimodalLiveLLMService    # With tools parameter
├── OpenAILLMContext                  # Context for function calling
├── context_aggregator                # Function calling support
└── llm.register_function()           # Function handler registration
```

### Benefits of Function Calling Approach
- ✅ **No text interception needed** - Works with Gemini Live's audio-to-audio architecture
- ✅ **AI decides when to act** - Natural conversation flow
- ✅ **Scalable architecture** - Easy to add more functions (calendar, SMS, etc.)
- ✅ **Maintains audio quality** - Full Gemini Live 24kHz audio processing
- ✅ **Error resilient** - Proper error handling and user feedback

## 🎯 **CRITICAL DEVELOPMENT METHODOLOGY**

### **For Future External Actions with Gemini Live:**

**⚠️ ALWAYS use Function Calling - NEVER use text interception!**

#### **Why Text Interception Fails:**
- **Gemini Live** = Audio-to-Audio pipeline (STT + LLM + TTS internally)
- **No TextFrames** are emitted for processors to intercept
- **Frame processors never see text** - they only see audio frames
- **100+ failed attempts** proved this approach doesn't work

#### **Why Function Calling Works:**
- **Built into Gemini Live** - AI natively calls functions during conversation
- **Natural decision making** - AI decides when conditions are met
- **Reliable execution** - Functions execute with proper error handling
- **Scalable design** - Easy to add calendar, SMS, database operations, etc.

#### **Function Calling Implementation Pattern:**

```python
# 1. Define Function Schema
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

function_schema = FunctionSchema(
    name="your_function_name",
    description="What this function does",
    properties={
        "param1": {"type": "string", "description": "Parameter description"},
        "param2": {"type": "string", "description": "Parameter description"}
    },
    required=["param1", "param2"]
)

tools = ToolsSchema(standard_tools=[function_schema])

# 2. Create Function Handler
async def handle_your_function(params: FunctionCallParams):
    try:
        args = params.arguments
        # Your logic here
        result = await your_external_action(args)
        await params.result_callback(result)
    except Exception as e:
        await params.result_callback({"success": False, "error": str(e)})

# 3. Configure Gemini Live with Function Calling
llm = GeminiMultimodalLiveLLMService(
    api_key=os.getenv("GEMINI_API_KEY"),
    tools=tools,  # CRITICAL: Add tools parameter
    system_instruction="""
    CRITICAL: When [specific condition], immediately call your_function_name.
    You have access to: your_function_name - description of what it does
    """
)

# 4. Register Function Handler
llm.register_function("your_function_name", handle_your_function)

# 5. CRITICAL: Add Context Aggregation (Required for Function Calling)
context = OpenAILLMContext(
    messages=[{
        "role": "system",
        "content": "SAME system instruction emphasizing function calling"
    }],
    tools=tools  # CRITICAL: Include tools in context
)
context_aggregator = llm.create_context_aggregator(context)

# 6. Pipeline with Context Aggregation
pipeline = Pipeline([
    transport.input(),
    context_aggregator.user(),      # REQUIRED
    llm,                           # Function calling enabled
    transport.output(),
    context_aggregator.assistant() # REQUIRED
])
```

#### **Critical Requirements:**
1. **✅ Tools parameter** in GeminiMultimodalLiveLLMService
2. **✅ Function registration** with llm.register_function()
3. **✅ OpenAILLMContext** with tools for function calling support
4. **✅ Context aggregators** in pipeline (user() and assistant())
5. **✅ Consistent system instructions** between service and context
6. **✅ Clear function calling instructions** in system prompt

#### **Common Pitfalls to Avoid:**
- ❌ **Don't use frame processors** for text interception with Gemini Live
- ❌ **Don't forget context aggregators** - function calls will fail
- ❌ **Don't have conflicting system instructions** - context overrides service
- ❌ **Don't skip tools parameter** in GeminiMultimodalLiveLLMService
- ❌ **Don't use different prompts** in service vs context

#### **Future Expansion Examples:**
```python
# Calendar Integration
calendar_function = FunctionSchema(
    name="add_to_calendar",
    description="Add appointment to Google Calendar",
    properties={"date": {"type": "string"}, "time": {"type": "string"}}
)

# SMS Integration
sms_function = FunctionSchema(
    name="send_sms_reminder",
    description="Send SMS appointment reminder",
    properties={"phone": {"type": "string"}, "message": {"type": "string"}}
)

# Database Operations
database_function = FunctionSchema(
    name="update_patient_record",
    description="Update patient information in database",
    properties={"patient_id": {"type": "string"}, "data": {"type": "object"}}
)
```

**This methodology enables unlimited external actions while maintaining Gemini Live's superior audio quality and natural conversation flow.**

### Email Integration Status
- ✅ **Web Interface** (`pipecat_server.py` - PORT 8091) - Full email integration with function calling
- ✅ **Phone Interface** (`twilio_pipecat_integrated.py` - PORT 8091) - Full email integration with function calling

Both interfaces now support complete appointment booking with automatic email confirmation!

## 📞 Twilio Phone Integration

### Overview
Complete phone-to-AI conversation system using Twilio Voice API with Media Streams. Callers can speak directly with the AI assistant through regular phone calls.

### Features
- ✅ **Incoming Calls** - Receive phone calls on Twilio number
- ✅ **Real-time Audio** - Bidirectional audio streaming via WebSocket
- ✅ **Auto Format Conversion** - Automatic mulaw ↔ PCM conversion at 8kHz
- ✅ **TwilioFrameSerializer** - Official Pipecat Twilio integration
- ✅ **Auto Hang-up** - Automatic call termination when conversation ends
- ✅ **Hospital Assistant** - Configured as "Archana" from Renova Hospitals
- ✅ **Phone Appointment Booking** - Full appointment booking via phone calls
- ✅ **Email Confirmations** - Automatic email confirmations for phone bookings
- ✅ **Function Calling** - Gemini Live function calling over phone calls

### Quick Setup Guide

#### 1. Twilio Configuration
```bash
# Add to .env file
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
NGROK_URL=https://your-ngrok-url.ngrok-free.app
```

#### 2. Start ngrok Tunnel
```bash
# Terminal 1: Start ngrok on port 8091
ngrok http 8091
# Copy the https URL (e.g., https://abc123.ngrok-free.app)
```

#### 3. Start Twilio Server
```bash
# Terminal 2: Start the integrated server
python src/twilio_pipecat_integrated.py
# Server runs on port 8091
```

#### 4. Configure Twilio Webhook
1. Go to **Twilio Console** → **Phone Numbers** → **Manage** → **Active Numbers**
2. Click your phone number (+1xxxxxxxxxx)
3. Set webhook URL: `https://your-ngrok-url.ngrok-free.app/`
4. HTTP method: `POST`
5. Save configuration

#### 5. Test Phone Calls
- Call +1xxxxxxxxxx
- Hear: "Hello! Connecting you to Archana, your Renova Hospital AI assistant."
- Start conversation with the AI

### Technical Implementation

#### TwiML Response (Webhook)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Hello! Connecting you to Archana, your Renova Hospital AI assistant.</Say>
    <Connect>
        <Stream url="wss://your-ngrok-url.ngrok-free.app/ws"></Stream>
    </Connect>
    <Pause length="40"/>
</Response>
```

#### TwilioFrameSerializer Configuration
```python
serializer = TwilioFrameSerializer(
    stream_sid=stream_sid,           # From Twilio WebSocket data
    call_sid=call_sid,               # From Twilio WebSocket data
    account_sid=TWILIO_ACCOUNT_SID,  # For authentication & auto hang-up
    auth_token=TWILIO_AUTH_TOKEN,    # For authentication & auto hang-up
)
```

#### Audio Processing Pipeline
```
Phone Call → Twilio (mulaw 8kHz) → WebSocket → TwilioFrameSerializer
→ Pipecat Pipeline → Gemini Live → Audio Response → Twilio → Phone
```

### Twilio Integration Flow

1. **Incoming Call** → Twilio receives call on +1xxxxxxxxxx
2. **Webhook Request** → `POST /` to your server
3. **TwiML Response** → Server returns XML with WebSocket URL
4. **Media Stream** → Twilio connects to `wss://your-url/ws`
5. **Audio Processing** → TwilioFrameSerializer handles format conversion
6. **AI Conversation** → Gemini Live processes speech and responds
7. **Auto Hang-up** → Call terminates when conversation ends

### File Structure
```
twilio_pipecat_integrated.py    # Main integration server
├── @app.post("/")              # Webhook handler (returns TwiML)
├── @app.websocket("/ws")       # Media Stream handler
├── run_pipecat_bot()          # Pipeline with TwilioFrameSerializer
├── GeminiMultimodalLiveLLMService # AI processing
└── FastAPIWebsocketTransport   # Audio transport

audio_bridge.py                 # Audio format utilities (legacy)
├── TwilioAudioBridge          # mulaw ↔ PCM conversion
├── mulaw_to_pcm()             # Audio decoding
└── pcm_to_mulaw()             # Audio encoding
```

### Troubleshooting Twilio

#### Common Issues
- **"Application Error"** → Check webhook URL includes `/` endpoint
- **No Audio** → Verify TwilioFrameSerializer has both stream_sid and call_sid
- **Connection Drops** → Check ngrok tunnel is active and accessible
- **Robotic Voice** → Ensure Gemini Live uses natural speech instructions

#### Debug Commands
```bash
# Test webhook endpoint
curl -X POST https://your-ngrok-url.ngrok-free.app/

# Check Twilio server health
curl https://your-ngrok-url.ngrok-free.app/health

# View active calls
curl https://your-ngrok-url.ngrok-free.app/twilio/calls

# Test ngrok tunnel
curl https://your-ngrok-url.ngrok-free.app/
```

#### Logs to Check
```
# Successful call flow:
INFO: Incoming call: CAxxxx from +1234567890 to +1xxxxxxxxxx, status: ringing
INFO: WebSocket connection accepted
INFO: Call data received: {'event': 'start', 'start': {'streamSid': 'MZxxxx'}}
INFO: Starting bot for stream: MZxxxx, call: CAxxxx
INFO: Starting Pipecat pipeline for Twilio call
DEBUG: Connecting to Gemini service
```

### Production Deployment

#### ngrok Alternatives for Production
```bash
# Option 1: Deploy to cloud with public IP
# Configure firewall to allow port 8091

# Option 2: Use reverse proxy (nginx)
# Configure SSL certificate and domain

# Option 3: Use cloud services (AWS/Google Cloud)
# Deploy with load balancer and auto-scaling
```

#### Webhook Security
```python
# Validate Twilio requests (recommended for production)
from twilio.request_validator import RequestValidator

validator = RequestValidator(TWILIO_AUTH_TOKEN)
is_valid = validator.validate(request_url, post_data, signature)
```

## Troubleshooting

### Common Issues & Solutions

#### Voice Quality Issues
- **❌ Robotic Voice**: Check audio sample rate - MUST use 24kHz output for natural speech
- **❌ No Greeting**: Ensure `LLMRunFrame()` is queued on client connection
- **❌ Poor Audio**: Verify ProtobufFrameSerializer is used (not JSON)
- **✅ Solution**: Use `audio_out_sample_rate=24000` in FastAPIWebsocketParams

#### Connection & Transport Issues
- **❌ DecodeError**: Frontend sending wrong format - use official Pipecat SDK
- **❌ CancelFrame Warnings**: Normal for interruption handling - can be ignored
- **❌ Port 8090 in use**: Kill existing servers or use different port
- **✅ Solution**: Use FastAPIWebsocketTransport with ProtobufFrameSerializer

#### Frontend Issues
- **❌ Voice Selection Not Working**: Check URL query parameter `?voice_id=Charon`
- **❌ Audio Not Playing**: Verify playerSampleRate matches server (24kHz)
- **❌ SDK Errors**: Install @pipecat-ai/client-js and @pipecat-ai/websocket-transport
- **✅ Solution**: Use PipecatVoiceChat component (not SimplePipecatClient)

#### Backend Issues
- **❌ Windows Signal Handling**: Use `PipelineRunner(handle_sigint=False)`
- **❌ Context Aggregator Error**: Don't use with GeminiMultimodalLiveLLMService
- **❌ Invalid Voice Config**: Use only voice_id parameter
- **❌ SileroVADAnalyzer Params**: Use default constructor `SileroVADAnalyzer()`
- **✅ Solution**: Use pipecat_server.py (production-ready)

### Debug Commands
```bash
# Check production server health
curl http://localhost:8090/health

# Check server status
curl http://localhost:8090/

# Test voice selection
# Connect to ws://localhost:8090/ws?voice_id=Kore

# Check logs
python src/pipecat_server.py  # View detailed logs
```

## 🎯 Critical Best Practices (LESSONS LEARNED)

### Audio Quality (Most Important!)
```python
# ✅ CORRECT: 24kHz output for natural voice
audio_out_sample_rate=24000,  # Fixes robotic voice!
audio_in_sample_rate=16000,   # Standard input

# ❌ WRONG: 16kHz output = robotic voice
audio_out_sample_rate=16000,  # Sounds robotic
```

### Voice Selection Implementation
```python
# ✅ CORRECT: Simple voice_id parameter
llm = GeminiMultimodalLiveLLMService(
    api_key=os.getenv("GEMINI_API_KEY"),
    voice_id=voice_id,  # Puck, Charon, Kore, Fenrir
    model="models/gemini-2.0-flash-exp"
)

# ❌ WRONG: Custom voice_config causes errors
voice_config={"style": "natural"}  # Not supported
```

### Natural Speech Instructions
```python
system_instruction="""
IMPORTANT SPEECH GUIDELINES:
- Speak like a real human with natural rhythm and flow
- Use contractions (I'm, you're, can't, won't)
- Add natural filler words occasionally (um, well, you know)
- Use emotional inflection - sound excited, concerned, or thoughtful
- Take natural pauses between sentences and thoughts
- Avoid monotone delivery - use pitch variation
"""
```

### Transport Configuration
```python
# ✅ CORRECT: Official transport with proper serializer
transport = FastAPIWebsocketTransport(
    websocket=websocket,
    params=FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        add_wav_header=False,
        vad_analyzer=SileroVADAnalyzer(),  # Default constructor only
        serializer=ProtobufFrameSerializer(),  # No extra params
        audio_out_sample_rate=24000,  # CRITICAL FOR QUALITY
    )
)
```

### 🔧 Function Calling for External Actions (Critical!)

**The ONLY way to perform external actions with Gemini Live**

#### ✅ **CORRECT: Function Calling Methodology**
```python
# 1. Define function schema
send_email_function = FunctionSchema(
    name="send_appointment_email",
    description="Send appointment confirmation email",
    properties={
        "patient_name": {"type": "string", "description": "Full name of patient"},
        "email": {"type": "string", "description": "Patient's email address"},
        "appointment_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
        # ... other properties
    },
    required=["patient_name", "email", "appointment_date", "appointment_time"]
)

# 2. Create tools schema
appointment_tools = ToolsSchema(standard_tools=[send_email_function])

# 3. Add tools to Gemini Live service
llm = GeminiMultimodalLiveLLMService(
    api_key=GEMINI_API_KEY,
    tools=appointment_tools,  # CRITICAL: Add tools here
    system_instruction="You have access to send_appointment_email function..."
)

# 4. Register function handler
llm.register_function("send_appointment_email", handle_send_appointment_email)

# 5. Create context with tools (required for function calling)
context = OpenAILLMContext(
    messages=[{"role": "system", "content": "..."}],
    tools=appointment_tools  # CRITICAL: Add tools to context
)

# 6. Add context aggregator to pipeline
context_aggregator = llm.create_context_aggregator(context)
pipeline = Pipeline([
    transport.input(),
    context_aggregator.user(),      # REQUIRED for function calling
    llm,
    transport.output(),
    context_aggregator.assistant()  # REQUIRED for function calling
])
```

#### ❌ **WRONG: Text Interception (Doesn't Work!)**
```python
# This FAILS with Gemini Live - audio-to-audio pipeline doesn't emit TextFrames
class EmailProcessor(FrameProcessor):
    async def process_frame(self, frame, direction):
        if isinstance(frame, TextFrame):  # This never happens!
            if "confirmed" in frame.text:
                send_email()  # Never triggered
```

**Why Text Interception Fails**: Gemini Live is an audio-to-audio pipeline that bypasses text frames entirely.

### 📅 **Date Interpretation for Appointment Booking**

#### ✅ **CORRECT: Provide Current Date Context**
```python
from datetime import datetime, timedelta

system_instruction=f"""
CURRENT DATE CONTEXT:
Today's date is: {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A, %B %d, %Y')})

DATE INTERPRETATION GUIDELINES:
- "today" = {datetime.now().strftime('%Y-%m-%d')}
- "tomorrow" = {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
- "day after tomorrow" = {(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')}
- Always convert dates to YYYY-MM-DD format when calling appointment functions
- If patient says relative dates like "tomorrow", convert to exact dates

APPOINTMENT BOOKING PROCESS:
4. Collect preferred date/time - ALWAYS convert relative dates to YYYY-MM-DD format
"""
```

#### ❌ **WRONG: No Date Context**
```python
# Without current date context, AI books wrong dates
system_instruction="Book appointments..."  # AI doesn't know what "tomorrow" means
```

**Result**: Patient says "tomorrow" → AI books appointment for random past date

### Windows Compatibility
```python
# ✅ CORRECT: Windows-compatible runner
runner = PipelineRunner(handle_sigint=False)  # For Windows

# ❌ WRONG: Default causes signal errors on Windows
runner = PipelineRunner()  # Fails on Windows
```

## Production Deployment

### Docker Production
```dockerfile
# Multi-stage build optimized for production
# Non-root user for security
# Health checks enabled
# Environment variable configuration
```

### Environment Setup
- Set production API keys
- Configure CORS origins
- Enable metrics collection
- Set appropriate session limits
- Configure logging levels

### Monitoring
- Health check endpoint for load balancers
- Structured JSON logs for log aggregation
- Metrics endpoint for monitoring systems
- Session cleanup automation

## 🔐 OAuth2 Authentication & Token Management

### Overview
The voice agent uses Google OAuth2 authentication for accessing Gmail and Calendar APIs. This section documents critical lessons learned during implementation and best practices for token management.

### ⚡ Quick Start Guide

#### 1. Authentication Setup
```bash
# 1. Place your Google OAuth2 credentials file
cp your-credentials.json server/gclientsec.json.json

# 2. Run any Google service to trigger OAuth flow
cd server/src
python gmail_service.py  # This will open browser for authentication

# 3. Verify token has all required scopes
python -c "
import pickle, requests
with open('google_token.pickle', 'rb') as f:
    creds = pickle.load(f)
response = requests.get(f'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={creds.token}')
scopes = response.json().get('scope', '').split()
print(f'Token has {len(scopes)} scopes:')
for scope in scopes: print(f'  - {scope}')
"
```

### 🔧 Authentication Architecture

#### Required Google API Scopes
```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',         # Send emails
    'https://www.googleapis.com/auth/gmail.readonly',     # Read Gmail profile
    'https://www.googleapis.com/auth/calendar',           # Access Calendar
    'https://www.googleapis.com/auth/calendar.events'     # Create/manage events
]
```

#### Token File Management
- **Location**: `server/src/google_token.pickle` AND `server/google_token.pickle`
- **Scope**: Single token with ALL required permissions
- **Sharing**: Both Gmail and Calendar services use the same token
- **Persistence**: Token refreshes automatically when expired

### 🚨 Critical Lessons Learned

#### ❌ **Common Pitfall: Multiple Token Files**
**Problem**: Creating separate tokens for Gmail and Calendar leads to scope conflicts.

```bash
# BAD: Different tokens with different scopes
server/google_token.pickle          # Only Gmail scopes (2 scopes)
server/src/google_token.pickle      # Gmail + Calendar scopes (4 scopes)
```

**Symptom**: Gmail works but Calendar fails with "insufficient authentication scopes"

**Root Cause**: Voice agent runs from `server/` directory, finds incomplete token

#### ✅ **Solution: Single Token Strategy**
```bash
# GOOD: Same complete token in both locations
server/google_token.pickle          # Gmail + Calendar scopes (4 scopes)
server/src/google_token.pickle      # Gmail + Calendar scopes (4 scopes)

# Copy command to sync tokens
cp server/src/google_token.pickle server/google_token.pickle
```

#### 🔄 **Token Refresh Issues**
**Problem**: Token refresh doesn't add new scopes automatically

**Solution**: Delete token file and re-authenticate when adding new scopes:
```bash
rm server/src/google_token.pickle
rm server/google_token.pickle
python gmail_service.py  # Triggers fresh OAuth with all scopes
```

#### 🔧 **Critical OAuth Fix: Missing Refresh Token Fields**
**Problem**: Token missing required fields for refresh operations

**Error Message**:
```
The credentials do not contain the necessary fields need to refresh the access token.
You must specify refresh_token, token_uri, client_id, and client_secret.
```

**Root Cause**: OAuth token created without proper refresh token configuration

**Solution**: Complete token recreation with proper OAuth flow:
```bash
# 1. Remove all existing token files
rm server/src/google_token.pickle
rm server/google_token.pickle

# 2. Create fresh token with all required fields
cd server/src
python -c "from googel_auth_manger import get_credentials; get_credentials()"

# 3. Copy token to both locations
cp google_token.pickle ../google_token.pickle

# 4. Verify both services work
python -c "
from gmail_service import get_gmail_service
from calendar_service import get_calendar_service

gmail = get_gmail_service()
calendar = get_calendar_service()

print('Gmail:', 'SUCCESS' if gmail.get_user_profile().get('success') else 'FAILED')
print('Calendar:', 'SUCCESS' if calendar.get_calendar_info().get('success') else 'FAILED')
"
```

### 📁 **File Structure & Dependencies**

```
server/
├── google_token.pickle                 # Complete token (voice agent uses this)
├── gclientsec.json.json               # OAuth2 credentials file
└── src/
    ├── googel_auth_manger.py          # Central authentication manager
    ├── gmail_service.py               # Gmail API service
    ├── calendar_service.py            # Calendar API service
    ├── appointment_functions.py       # Function calling with both services
    └── google_token.pickle            # Complete token (manual tests use this)
```

### 🧪 **Testing Authentication**

#### Verify Token Scopes
```python
import pickle, requests, os

def check_token_scopes(token_path):
    if not os.path.exists(token_path):
        return f"❌ Token not found: {token_path}"

    with open(token_path, 'rb') as f:
        creds = pickle.load(f)

    if not creds.valid:
        return f"❌ Token invalid: {token_path}"

    try:
        response = requests.get(f'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={creds.token}')
        scopes = response.json().get('scope', '').split()
        required = ['gmail.send', 'gmail.readonly', 'calendar', 'calendar.events']

        result = f"✅ Token valid: {token_path}\n"
        result += f"   Scopes: {len(scopes)}/4 required\n"

        for req in required:
            has_scope = any(req in scope for scope in scopes)
            status = "✅" if has_scope else "❌"
            result += f"   {status} {req}\n"

        return result
    except Exception as e:
        return f"❌ Token check failed: {e}"

# Test both token locations
print(check_token_scopes('server/google_token.pickle'))
print(check_token_scopes('server/src/google_token.pickle'))
```

#### Test Both Services
```python
# Test Gmail service
from gmail_service import get_gmail_service
gmail = get_gmail_service()
profile = gmail.get_user_profile()
print(f"Gmail: {'✅' if profile.get('success') else '❌'}")

# Test Calendar service
from calendar_service import get_calendar_service
calendar = get_calendar_service()
info = calendar.get_calendar_info()
print(f"Calendar: {'✅' if info.get('success') else '❌'}")
```

### 🛠️ **Troubleshooting Guide**

#### Error: "Request had insufficient authentication scopes"
```bash
# 1. Check which token the service is using
python -c "
import os
print('Voice agent working directory:', os.getcwd())
print('Token exists:', os.path.exists('google_token.pickle'))
"

# 2. Check token scopes (use verification script above)

# 3. Copy complete token if needed
cp src/google_token.pickle google_token.pickle

# 4. If token is incomplete, delete and re-authenticate
rm google_token.pickle src/google_token.pickle
python src/gmail_service.py
```

#### Error: "Token refresh failed"
```bash
# Token corruption - force fresh authentication
rm google_token.pickle src/google_token.pickle
python src/calendar_service.py  # Will trigger OAuth flow
```

#### Working Directory Issues
```python
# Always use absolute paths in production
import os
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "google_token.pickle")

# Or ensure both locations have complete tokens
# server/google_token.pickle (for voice agent)
# server/src/google_token.pickle (for manual testing)
```

### 🎯 **Best Practices**

#### ✅ **DO**
- Use single token file with ALL required scopes
- Keep tokens synchronized between `server/` and `server/src/`
- Test both Gmail and Calendar services after authentication
- Use absolute paths for token files in production
- Check token scopes before deploying

#### ❌ **DON'T**
- Create separate tokens for different services
- Assume token refresh adds new scopes
- Hardcode relative paths for critical files
- Skip scope verification after authentication
- Commit token files to version control

### 📋 **Pre-Deployment Checklist**
- [ ] OAuth2 credentials file in correct location
- [ ] Token file exists in both `server/` and `server/src/`
- [ ] Token has all 4 required scopes (Gmail + Calendar)
- [ ] Gmail service test passes
- [ ] Calendar service test passes
- [ ] Appointment function creates both email and calendar event
- [ ] Voice agent runs without authentication errors

## 🌐 Google Services Integration Guidelines

### Overview
This section provides comprehensive guidelines for integrating Google services (Gmail, Calendar, Drive, etc.) based on lessons learned during OAuth implementation and troubleshooting.

### 🚀 **Quick Integration Checklist**

When adding any new Google service, follow this proven methodology:

#### 1. **Scope Planning** (Before Coding)
```python
# Always plan ALL scopes upfront - adding later causes token conflicts
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',         # Existing
    'https://www.googleapis.com/auth/gmail.readonly',     # Existing
    'https://www.googleapis.com/auth/calendar',           # Existing
    'https://www.googleapis.com/auth/calendar.events',    # Existing
    'https://www.googleapis.com/auth/drive.file',         # NEW: If adding Drive
    'https://www.googleapis.com/auth/sheets',             # NEW: If adding Sheets
]
```

#### 2. **Service Creation Pattern**
```python
# Use this template for any new Google service
class NewGoogleService:
    def __init__(self):
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Standard initialization pattern"""
        try:
            creds = get_credentials()  # Uses central auth manager
            self.service = build('servicename', 'version', credentials=creds)

            # Test the service immediately
            test_result = self.service.about().get().execute()  # Adjust per service
            logger.info(f"Service initialized: {test_result.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Failed to initialize service: {str(e)}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """Always include a test method"""
        try:
            # Service-specific test call
            result = self.service.about().get().execute()
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

#### 3. **Token Management Protocol**
```bash
# CRITICAL: When adding new scopes, ALWAYS follow this sequence:

# Step 1: Update SCOPES in googel_auth_manger.py
# Step 2: Delete ALL existing tokens
rm server/google_token.pickle server/src/google_token.pickle

# Step 3: Create fresh token with ALL scopes
cd server/src
python -c "from googel_auth_manger import get_credentials; get_credentials()"

# Step 4: Copy to both locations
cp google_token.pickle ../google_token.pickle

# Step 5: Test ALL services
python -c "
from gmail_service import get_gmail_service
from calendar_service import get_calendar_service
# Add tests for new services here

print('All services tested successfully')
"
```

### 🔧 **Common Google Services Integration Patterns**

#### **Gmail API Integration**
```python
# Proven pattern for email operations
def send_email(to: str, subject: str, body: str, is_html: bool = False):
    try:
        service = build('gmail', 'v1', credentials=get_credentials())

        message = MIMEText(body, 'html' if is_html else 'plain')
        message['to'] = to
        message['subject'] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        return {'success': True, 'message_id': result['id']}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

#### **Google Calendar API Integration**
```python
# Proven pattern for calendar operations
def create_calendar_event(summary: str, start_time: datetime, end_time: datetime):
    try:
        service = build('calendar', 'v3', credentials=get_credentials())

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata',  # Always specify timezone
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        result = service.events().insert(calendarId='primary', body=event).execute()
        return {'success': True, 'event_id': result['id']}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

#### **Google Drive API Integration**
```python
# Template for Drive integration (if needed)
def upload_to_drive(file_path: str, folder_id: str = None):
    try:
        service = build('drive', 'v3', credentials=get_credentials())

        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id] if folder_id else []
        }

        media = MediaFileUpload(file_path)

        result = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()

        return {'success': True, 'file_id': result['id'], 'link': result['webViewLink']}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### ⚠️ **Critical Don'ts for Google Services**

#### ❌ **Never Do These**
1. **Create separate OAuth tokens for different services**
   ```python
   # BAD: Multiple tokens
   gmail_creds = get_gmail_credentials()  # ❌ Wrong approach
   calendar_creds = get_calendar_credentials()  # ❌ Wrong approach

   # GOOD: Single token with all scopes
   creds = get_credentials()  # ✅ Correct approach
   ```

2. **Add scopes to existing tokens**
   ```python
   # BAD: Trying to add scopes to existing token
   # This will fail with "insufficient scopes" error

   # GOOD: Delete token and recreate with all scopes
   ```

3. **Ignore timezone handling**
   ```python
   # BAD: No timezone specified
   'start': {'dateTime': start_time.isoformat()}  # ❌ Timezone issues

   # GOOD: Always specify timezone
   'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'}  # ✅
   ```

4. **Skip error handling**
   ```python
   # BAD: No error handling
   service.events().insert(calendarId='primary', body=event).execute()  # ❌

   # GOOD: Comprehensive error handling
   try:
       result = service.events().insert(calendarId='primary', body=event).execute()
       return {'success': True, 'data': result}
   except HttpError as e:
       return {'success': False, 'error': f'API Error: {e}'}
   ```

### 🧪 **Testing Strategy for Google Services**

#### **Service Health Check Pattern**
```python
def test_all_google_services():
    """Test all Google services to ensure proper integration"""
    results = {}

    # Test Gmail
    try:
        gmail = get_gmail_service()
        results['gmail'] = gmail.get_user_profile().get('success', False)
    except Exception as e:
        results['gmail'] = f"Error: {e}"

    # Test Calendar
    try:
        calendar = get_calendar_service()
        results['calendar'] = calendar.get_calendar_info().get('success', False)
    except Exception as e:
        results['calendar'] = f"Error: {e}"

    # Add more services as needed

    return results
```

#### **Integration Test for Function Calling**
```python
def test_appointment_integration():
    """Test complete appointment flow with both email and calendar"""
    try:
        # Test email sending
        email_result = send_appointment_email_test()

        # Test calendar creation
        calendar_result = create_calendar_event_test()

        # Test both together
        both_success = email_result.get('success') and calendar_result.get('success')

        return {
            'email': email_result.get('success'),
            'calendar': calendar_result.get('success'),
            'integration': both_success
        }
    except Exception as e:
        return {'error': str(e)}
```

### 📋 **Google Services Development Checklist**

Before deploying any Google service integration:

- [ ] **Scope Planning**: All required scopes identified upfront
- [ ] **Single Token**: One OAuth token for all services
- [ ] **Error Handling**: Comprehensive try/catch blocks
- [ ] **Timezone Handling**: Explicit timezone specification
- [ ] **Test Methods**: Health check for each service
- [ ] **Integration Tests**: Cross-service functionality tested
- [ ] **Token Backup**: Token files in both server locations
- [ ] **Documentation**: Service patterns documented
- [ ] **Rate Limiting**: API rate limits considered
- [ ] **Security**: No credentials in code or git

### 🎯 **Future Google Service Additions**

When adding new Google services (Sheets, Drive, Photos, etc.):

1. **Plan scopes** before writing any code
2. **Update `googel_auth_manger.py`** with new scopes
3. **Delete all tokens** and recreate fresh
4. **Follow service creation pattern** shown above
5. **Add comprehensive tests** for the new service
6. **Update this documentation** with new patterns

This methodology ensures smooth integration without the OAuth issues we encountered during development.

## Future Enhancements

### Planned Features
- **Authentication** - JWT-based session authentication
- **Rate Limiting** - API rate limiting and abuse prevention
- **Database Integration** - Session persistence and analytics
- **Load Balancing** - Multi-instance deployment support
- **Metrics Dashboard** - Real-time monitoring interface

### Scalability
- **Horizontal Scaling** - Multiple server instances
- **Session Persistence** - Redis-based session storage
- **Audio Recording** - Conversation logging and playback
- **Multi-language Support** - International voice models

## License & Credits

### Technologies Used
- **Pipecat AI** - Voice agent framework
- **Google Gemini Live** - Unified voice processing
- **React** - Frontend framework
- **FastAPI** - Python web framework
- **WebRTC** - Real-time communication

### API Credits
- **Gemini API Key**: your_gemini_api_key_here
- **Rate Limits**: Monitor usage in Google AI Studio
- **Billing**: Pay-per-use model for Gemini Live API

---

*This project demonstrates a complete voice agent implementation with modern web technologies, self-hosted infrastructure, and production-ready deployment capabilities.*