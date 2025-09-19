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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Simple Enhanced Pipecat server")
    yield
    logger.info("Shutting down Simple Enhanced Pipecat server")

# Create FastAPI app
app = FastAPI(
    title="Renova Hospitals Voice Agent - Enhanced",
    description="Voice agent with availability checking, call logging, and appointment cancellation",
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

def get_simple_system_instruction(voice_id: str = "Charon") -> str:
    """Get simple system instructions - English first, can switch if asked"""

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    return f"""
🏥 RENOVA HOSPITALS VOICE AGENT

You are a helpful voice assistant for Renova Hospitals.

=== CURRENT CONTEXT ===
Today's date: {today.strftime('%Y-%m-%d (%A)')}
Tomorrow's date: {tomorrow.strftime('%Y-%m-%d (%A)')}
Current time: {today.strftime('%H:%M')}
Voice: {voice_id} (24kHz natural audio)

=== LANGUAGE POLICY ===
- Start in English by default
- If user asks for Hindi or Telugu, switch to that language
- Keep names, emails, phone numbers, and medical terms in English always
- Example: "मैं Dr. Patel के साथ appointment book करूंगा" (mixing is fine)

=== ENHANCED WORKFLOW ===

🔍 FOR APPOINTMENT BOOKING:
1. ALWAYS check availability first using check_appointment_availability()
2. If slot is busy, offer alternatives
3. If available, collect all details and book using book_appointment()
4. Never book without checking availability first!

❌ FOR APPOINTMENT CANCELLATION:
1. Get patient name, doctor name, date, and time
2. Use cancel_appointment() to verify and cancel
3. Only cancels if details match exactly

📊 FOR GENERAL CALLS:
1. Help with hospital information
2. Log the call using log_call_information()

=== FUNCTION CALLING ===

Check availability:
```
check_appointment_availability(
    appointment_date="YYYY-MM-DD",
    appointment_time="HH:MM AM/PM"
)
```

Book appointment:
```
book_appointment(
    patient_name="John Smith",
    email="john@example.com",
    phone="+91-9876543210",
    appointment_date="YYYY-MM-DD",
    appointment_time="HH:MM AM/PM",
    doctor_name="Dr. Patel",
    department="Cardiology",
    customer_type="new",
    language_used="english"
)
```

Cancel appointment:
```
cancel_appointment(
    patient_name="John Smith",
    appointment_date="YYYY-MM-DD",
    appointment_time="HH:MM AM/PM",
    doctor_name="Dr. Patel",
    language_used="english"
)
```

Log call info:
```
log_call_information(
    customer_name="John Smith",
    call_type="general_enquiry",
    call_summary="Asked about visiting hours",
    language_used="english"
)
```

=== HOSPITAL INFO ===
- Departments: Cardiology, Neurology, Orthopedics, Pediatrics, General Medicine, Emergency
- Hours: 9 AM - 6 PM (Monday to Saturday)
- Emergency: 24/7

=== SIMPLE FLOW ===
1. Greet in English
2. If user asks for Hindi/Telugu, switch language
3. For appointments: check availability → book if free → confirm
4. For cancellations: verify details → cancel if match
5. For enquiries: provide info → log call

Keep it simple, helpful, and professional!
"""

async def create_simple_voice_session(websocket: WebSocket, voice_id: str = "Charon"):
    """Create simple enhanced voice session"""

    try:
        # Create simple system instruction
        system_instruction = get_simple_system_instruction(voice_id)

        # Create Gemini Live LLM service with enhanced tools
        llm = GeminiMultimodalLiveLLMService(
            api_key=os.getenv("GEMINI_API_KEY"),
            voice_id=voice_id,
            audio_out_sample_rate=24000,  # Critical for natural voice
            audio_in_sample_rate=16000,
            tools=enhanced_appointment_tools,  # Enhanced tools
            system_instruction=system_instruction
        )

        # Register enhanced functions
        for func_name, func_handler in ENHANCED_FUNCTION_REGISTRY.items():
            llm.register_function(func_name, func_handler)
            logger.info(f"Registered function: {func_name}")

        # Create context for function calling (REQUIRED!)
        context = OpenAILLMContext(tools=enhanced_appointment_tools)
        context_aggregator = llm.create_context_aggregator(context)

        # Create transport
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                vad_analyzer=SileroVADAnalyzer(),
                serializer=ProtobufFrameSerializer(),
                audio_out_sample_rate=24000,
                audio_in_sample_rate=16000,
                add_wav_header=False,
                vad_enabled=True,
                vad_audio_passthrough=True,
            )
        )

        # Create simple pipeline - no complications!
        pipeline = Pipeline([
            transport.input(),
            context_aggregator.user(),      # Required for function calling
            llm,                           # Gemini with enhanced functions
            transport.output(),
            context_aggregator.assistant() # Required for function calling
        ])

        # Create and start task
        task = PipelineTask(pipeline)

        logger.info(f"Starting simple session with voice: {voice_id}")

        # Queue initial greeting
        await task.queue_frames([LLMRunFrame()])

        # Create session info
        session_info = {
            "task": task,
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
    """Simple WebSocket endpoint"""

    await websocket.accept()
    logger.info("WebSocket connection established")

    # Get voice from query parameters
    query_params = websocket.query_params
    voice_id = query_params.get("voice_id", "Charon")
    session_id = query_params.get("session_id", "default")

    logger.info(f"Creating session - Voice: {voice_id}, Session: {session_id}")

    try:
        # Create simple voice session
        session_info = await create_simple_voice_session(websocket, voice_id)
        active_sessions[session_id] = session_info

        # Run the session
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(session_info["task"])

    except Exception as e:
        logger.error(f"WebSocket session error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        # Cleanup
        if session_id in active_sessions:
            session_info = active_sessions[session_id]
            duration = (datetime.now() - session_info["start_time"]).total_seconds()
            logger.info(f"Session ended - Duration: {duration}s")
            del active_sessions[session_id]

        logger.info(f"WebSocket connection closed for session: {session_id}")

@app.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "server": "Renova Hospitals Voice Agent - Enhanced & Simple",
        "features": {
            "availability_checking": True,
            "call_logging": True,
            "appointment_cancellation": True,
            "email_integration": True,
            "calendar_integration": True,
            "multi_language": "on_request"
        },
        "active_sessions": len(active_sessions),
        "supported_voices": ["Puck", "Charon", "Kore", "Fenrir"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/call-stats")
async def get_call_statistics():
    """Get call statistics"""
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

    parser = argparse.ArgumentParser(description="Simple Enhanced Voice Agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8090, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    print("Renova Hospitals Voice Agent - Enhanced & Simple")
    print("Features: Availability Check, Call Logging, Cancellation")
    print("Language: English (can switch to Hindi/Telugu on request)")
    print(f"Server: http://{args.host}:{args.port}")
    print(f"WebSocket: ws://{args.host}:{args.port}/ws?voice_id=Charon")
    print("=" * 60)

    uvicorn.run(
        "simple_enhanced_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )