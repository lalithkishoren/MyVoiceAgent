#!/usr/bin/env python3

import asyncio
import os
import sys
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog

# Pipecat imports
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.frames.frames import LLMRunFrame, EndFrame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

# Load environment variables
load_dotenv()

# Configure logging
logger = structlog.get_logger(__name__)

# Global variables
active_sessions = {}

# Import enhanced functionality
from gmail_routes import router as gmail_router
from enhanced_appointment_functions import (
    enhanced_appointment_tools,
    ENHANCED_FUNCTION_REGISTRY
)
from call_logger import get_call_logger
from language_support import get_language_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Enhanced Pipecat server with multi-language support")
    yield
    logger.info("Shutting down Enhanced Pipecat server")

# Create FastAPI app
app = FastAPI(
    title="Enhanced Renova Hospitals Voice Agent",
    description="Multi-language voice agent with appointment booking, cancellation, and comprehensive call logging",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Gmail routes
app.include_router(gmail_router, prefix="/gmail", tags=["gmail"])

def get_enhanced_system_instruction(language: str = "english", voice_id: str = "Charon") -> str:
    """Get enhanced system instructions with multi-language support"""

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    lang_manager = get_language_manager()
    lang_specific_instruction = lang_manager.get_system_instruction_for_language(language)

    base_instruction = f"""
🏥 RENOVA HOSPITALS VOICE AGENT - ENHANCED VERSION 2.0

You are an advanced voice assistant for Renova Hospitals with comprehensive capabilities.

=== CRITICAL WORKFLOW ===
1. ALWAYS detect user's language preference first
2. ALWAYS check appointment availability BEFORE booking
3. ALWAYS log comprehensive call information
4. ALWAYS use function calling for external actions

=== CURRENT CONTEXT ===
Today's date: {today.strftime('%Y-%m-%d (%A)')}
Tomorrow's date: {tomorrow.strftime('%Y-%m-%d (%A)')}
Current time: {today.strftime('%H:%M')}
Voice: {voice_id} (24kHz natural audio)

{lang_specific_instruction}

=== NEW ENHANCED CAPABILITIES ===

🔍 AVAILABILITY CHECKING:
- ALWAYS call check_appointment_availability() before booking
- If slot unavailable, offer alternatives immediately
- Suggest nearby time slots and alternative dates

📅 APPOINTMENT BOOKING WORKFLOW:
1. Check availability first (required!)
2. Collect: name (English), phone, email, date, time, doctor, department
3. Verify customer type (new/existing)
4. Call book_appointment() which handles:
   - Final availability check
   - Email confirmation
   - Calendar integration
   - Automatic call logging

❌ APPOINTMENT CANCELLATION:
- Verify ALL details: name, doctor, date, time
- Call cancel_appointment() for verification
- Only cancel if details match exactly
- Send cancellation confirmation email

📊 CALL LOGGING:
- Log ALL calls with comprehensive information
- Include: customer details, call type, department/doctor enquired
- Track resolution status and language used
- Use log_call_information() for general enquiries

🌐 MULTI-LANGUAGE SUPPORT:
- Detect language from: "hindi", "हिंदी", "telugu", "తెలుగు"
- Respond in user's preferred language
- Keep names, emails, medical terms in English
- Format confirmations in appropriate language

=== FUNCTION CALLING REQUIREMENTS ===

FOR AVAILABILITY CHECKS:
```
check_appointment_availability(
    appointment_date="YYYY-MM-DD",
    appointment_time="HH:MM AM/PM",
    duration_minutes=30
)
```

FOR BOOKING APPOINTMENTS:
```
book_appointment(
    patient_name="John Smith",  # English only
    email="john@example.com",
    phone="+91-9876543210",
    appointment_date="YYYY-MM-DD",
    appointment_time="HH:MM AM/PM",
    doctor_name="Dr. Patel",  # English only
    department="Cardiology",
    customer_type="new|existing",
    language_used="english|hindi|telugu"
)
```

FOR CANCELLATION:
```
cancel_appointment(
    patient_name="John Smith",
    patient_email="john@example.com",
    patient_phone="+91-9876543210",
    appointment_date="YYYY-MM-DD",
    appointment_time="HH:MM AM/PM",
    doctor_name="Dr. Patel",
    language_used="english|hindi|telugu"
)
```

FOR GENERAL CALL LOGGING:
```
log_call_information(
    customer_name="John Smith",
    customer_phone="+91-9876543210",
    customer_email="john@example.com",
    call_type="general_enquiry|department_enquiry|doctor_enquiry|billing_enquiry|emergency|other",
    customer_type="new|existing|unknown",
    department_enquired="Cardiology",
    doctor_enquired="Dr. Patel",
    call_summary="Brief summary of conversation",
    resolution_status="resolved|partially_resolved|unresolved|escalated|follow_up_required",
    language_used="english|hindi|telugu"
)
```

=== CONVERSATION FLOW ===

🎯 APPOINTMENT BOOKING:
1. "Let me check availability for that time slot..."
2. Call check_appointment_availability()
3. If available: "Great! That slot is free. Let me book it for you."
4. If unavailable: "Sorry, that slot is busy. Here are alternatives: [list options]"
5. Collect all required details
6. Call book_appointment()
7. Confirm success with appropriate language

🎯 APPOINTMENT CANCELLATION:
1. "To cancel, I need to verify some details..."
2. Collect: name, doctor, date, time (and email/phone if available)
3. Call cancel_appointment()
4. If successful: confirm cancellation
5. If failed: "Details don't match. Please verify and try again."

🎯 GENERAL ENQUIRIES:
1. Provide helpful information
2. Call log_call_information() with appropriate call_type
3. Include department/doctor if mentioned

=== HOSPITAL INFORMATION ===
- Departments: Cardiology, Neurology, Orthopedics, Pediatrics, General Medicine, Emergency, Dermatology, Gastroenterology
- Visiting Hours: 9 AM - 6 PM (Monday to Saturday)
- Emergency: 24/7 available
- Location: Multiple branches in the city

=== ERROR HANDLING ===
- If function calls fail, inform user and offer alternatives
- For partial failures, explain what succeeded and what didn't
- Always maintain professional, helpful tone
- Offer to transfer to human agent for complex issues

=== CRITICAL REMINDERS ===
1. NEVER book without checking availability first
2. ALWAYS use function calling for external actions
3. ALWAYS log calls for tracking and analytics
4. ALWAYS keep names and emails in English
5. ALWAYS respond in user's preferred language
6. ALWAYS be respectful and professional

Remember: You're representing Renova Hospitals' commitment to excellent patient care through advanced technology.
"""

    return base_instruction


async def create_voice_session(websocket: WebSocket, voice_id: str = "Charon", language: str = "english"):
    """Create enhanced voice session with all new features"""

    try:
        # Set language context
        lang_manager = get_language_manager()
        lang_manager.set_language(language)

        # Create enhanced system instruction
        system_instruction = get_enhanced_system_instruction(language, voice_id)

        # Create Gemini Live LLM service with enhanced tools
        llm = GeminiMultimodalLiveLLMService(
            api_key=os.getenv("GEMINI_API_KEY"),
            voice_id=voice_id,
            audio_out_sample_rate=24000,  # Critical for natural voice
            audio_in_sample_rate=16000,
            tools=enhanced_appointment_tools,  # Enhanced tools with all new functions
            system_instruction=system_instruction
        )

        # Register ALL enhanced functions
        for func_name, func_handler in ENHANCED_FUNCTION_REGISTRY.items():
            llm.register_function(func_name, func_handler)
            logger.info(f"Registered enhanced function: {func_name}")

        # Create context for function calling (CRITICAL!)
        context = OpenAILLMContext(tools=enhanced_appointment_tools)
        context_aggregator = llm.create_context_aggregator(context)

        # Create transport with optimal settings
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                vad_analyzer=SileroVADAnalyzer(),
                serializer=ProtobufFrameSerializer(),
                audio_out_sample_rate=24000,  # High quality audio output
                audio_in_sample_rate=16000,   # Standard input
                add_wav_header=False,
                vad_enabled=True,
                vad_audio_passthrough=True,
            )
        )

        # Create enhanced pipeline (simplified - language detection in system instructions)
        pipeline = Pipeline([
            transport.input(),
            context_aggregator.user(),
            llm,
            transport.output(),
            context_aggregator.assistant(),
        ])

        # Create and start task
        task = PipelineTask(pipeline)

        # Start with greeting that includes language detection
        greeting_text = lang_manager.get_text("greeting", language)
        logger.info(f"Starting session with voice: {voice_id}, language: {language}")
        logger.info(f"Greeting: {greeting_text}")

        # Queue initial greeting
        await task.queue_frames([LLMRunFrame()])

        # Create session info
        session_info = {
            "task": task,
            "language": language,
            "voice_id": voice_id,
            "start_time": datetime.now(),
            "call_logger": get_call_logger()
        }

        return session_info

    except Exception as e:
        logger.error(f"Failed to create voice session: {e}")
        raise

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint with multi-language support"""

    await websocket.accept()
    logger.info("Enhanced WebSocket connection established")

    # Get voice and language from query parameters
    query_params = websocket.query_params
    voice_id = query_params.get("voice_id", "Charon")
    language = query_params.get("language", "english").lower()
    session_id = query_params.get("session_id", "default")

    # Validate language
    if language not in ["english", "hindi", "telugu"]:
        language = "english"

    logger.info(f"Creating enhanced session - Voice: {voice_id}, Language: {language}, Session: {session_id}")

    try:
        # Create enhanced voice session
        session_info = await create_voice_session(websocket, voice_id, language)
        active_sessions[session_id] = session_info

        # Run the session
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(session_info["task"])

    except Exception as e:
        logger.error(f"Enhanced WebSocket session error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        # Cleanup
        if session_id in active_sessions:
            session_info = active_sessions[session_id]

            # Log session end
            call_logger = session_info.get("call_logger")
            if call_logger:
                try:
                    duration = (datetime.now() - session_info["start_time"]).total_seconds()
                    logger.info(f"Session ended - Duration: {duration}s, Language: {session_info['language']}")
                except Exception as e:
                    logger.warning(f"Failed to log session end: {e}")

            del active_sessions[session_id]

        logger.info(f"Enhanced WebSocket connection closed for session: {session_id}")

@app.get("/health")
async def health_check():
    """Enhanced health check with feature status"""
    return {
        "status": "healthy",
        "server": "Enhanced Renova Hospitals Voice Agent v2.0",
        "features": {
            "multi_language": True,
            "availability_checking": True,
            "call_logging": True,
            "appointment_cancellation": True,
            "email_integration": True,
            "calendar_integration": True
        },
        "active_sessions": len(active_sessions),
        "supported_languages": ["english", "hindi", "telugu"],
        "supported_voices": ["Puck", "Charon", "Kore", "Fenrir"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/sessions")
async def get_active_sessions():
    """Get information about active sessions"""
    session_info = {}
    for session_id, session in active_sessions.items():
        session_info[session_id] = {
            "language": session.get("language", "unknown"),
            "voice_id": session.get("voice_id", "unknown"),
            "start_time": session.get("start_time", "unknown"),
            "duration_seconds": (datetime.now() - session.get("start_time", datetime.now())).total_seconds()
        }

    return {
        "active_sessions": len(active_sessions),
        "sessions": session_info
    }

@app.get("/call-stats")
async def get_call_statistics():
    """Get call statistics from the logger"""
    try:
        call_logger = get_call_logger()
        stats = call_logger.get_call_stats(days=30)
        return {
            "success": True,
            "stats": stats,
            "period": "last_30_days"
        }
    except Exception as e:
        logger.error(f"Failed to get call stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Run server
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Renova Hospitals Voice Agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8090, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    print("🏥 Starting Enhanced Renova Hospitals Voice Agent v2.0")
    print(f"🔊 Voice Options: Puck, Charon, Kore, Fenrir")
    print(f"🌐 Languages: English, Hindi (हिंदी), Telugu (తెలుగు)")
    print(f"✨ Features: Availability Check, Multi-language, Call Logging, Cancellation")
    print(f"🌍 Server: http://{args.host}:{args.port}")
    print(f"📡 WebSocket: ws://{args.host}:{args.port}/ws?voice_id=Charon&language=english")
    print(f"💚 Health: http://{args.host}:{args.port}/health")
    print("=" * 80)

    uvicorn.run(
        "enhanced_pipecat_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )