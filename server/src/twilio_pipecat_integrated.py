#!/usr/bin/env python3

import os
import sys
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
import structlog

# Twilio imports - using raw XML due to Windows path length issues
# from twilio.twiml.voice_response import VoiceResponse, Stream, Connect

# Pipecat imports
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.frames.frames import LLMRunFrame, EndFrame
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

# Import email functionality
from appointment_functions import appointment_tools, handle_send_appointment_email

# Load environment variables
load_dotenv()

# Configure logging
logger = structlog.get_logger(__name__)

# Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8091"))

# Global variables
active_calls = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Integrated Twilio-Pipecat Server")
    logger.info(f"Twilio Phone Number: {TWILIO_PHONE_NUMBER}")
    logger.info(f"Server running on {HOST}:{PORT}")
    yield
    logger.info("Shutting down Integrated Twilio-Pipecat Server")

# FastAPI app
app = FastAPI(
    title="Integrated Twilio-Pipecat Voice Server",
    description="Direct Twilio Media Streams integration with Pipecat",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "message": "Integrated Twilio-Pipecat Voice Server with Email Integration",
        "status": "running",
        "phone_number": TWILIO_PHONE_NUMBER,
        "webhook_url": f"http://{HOST}:{PORT}/",
        "stream_url": f"ws://{HOST}:{PORT}/ws",
        "active_calls": len(active_calls),
        "features": [
            "Voice calls via Twilio",
            "Appointment booking",
            "Automatic email confirmations",
            "Gemini Live function calling",
            "Natural voice interaction"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Test Gmail integration
    gmail_status = False
    try:
        from gmail_service import get_gmail_service
        gmail_service = get_gmail_service()
        profile = gmail_service.get_user_profile()
        gmail_status = profile.get('success', False)
    except Exception:
        gmail_status = False

    return {
        "status": "healthy",
        "service": "twilio-pipecat-integration-with-email",
        "active_calls": len(active_calls),
        "twilio_configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
        "gemini_configured": bool(GEMINI_API_KEY),
        "gmail_configured": gmail_status,
        "features": {
            "voice_calls": True,
            "appointment_booking": True,
            "email_confirmation": gmail_status,
            "function_calling": True
        }
    }

@app.post("/")
async def handle_incoming_call():
    """Handle incoming Twilio voice calls with webhook."""
    try:
        # Create TwiML response directly
        public_url = os.getenv("NGROK_URL", "https://3b5e8b96f9be.ngrok-free.app")
        stream_url = f"{public_url.replace('https://', 'wss://')}/ws"

        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Hello! Connecting you to Archana, your Renova Hospital AI assistant.</Say>
    <Connect>
        <Stream url="{stream_url}"></Stream>
    </Connect>
    <Pause length="40"/>
</Response>"""

        logger.info(f"Generated TwiML with stream URL: {stream_url}")
        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")

        # Fallback TwiML response
        fallback_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, there was an error processing your call. Please try again later.</Say>
</Response>"""
        return Response(content=fallback_response, media_type="application/xml")

async def run_pipecat_bot(websocket: WebSocket, stream_sid: str, call_sid: str):
    """Run a Pipecat bot using Twilio transport."""
    try:
        # Create Twilio serializer with proper authentication (matches official docs)
        serializer = TwilioFrameSerializer(
            stream_sid=stream_sid,
            call_sid=call_sid,
            account_sid=TWILIO_ACCOUNT_SID,
            auth_token=TWILIO_AUTH_TOKEN,
        )

        # Create Twilio WebSocket transport with Twilio-specific serializer
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_analyzer=SileroVADAnalyzer(),
                serializer=serializer,
                # Twilio audio settings
                audio_out_sample_rate=8000,  # Twilio uses 8kHz
                audio_in_sample_rate=8000,
                audio_out_channels=1,
            )
        )

        # Initialize Gemini Multimodal Live service with function calling
        llm = GeminiMultimodalLiveLLMService(
            api_key=GEMINI_API_KEY,
            voice_id="Charon",  # Using Charon voice for Archana
            model="models/gemini-2.0-flash-exp",
            tools=appointment_tools,  # Add appointment function tools
            # System instruction for Archana - Renova Hospital assistant with appointment booking
            system_instruction=f"""You are Archana, a patient service voice assistant for Renova Hospitals.

Your main role is to answer patient questions briefly, clearly, and politely regarding our services, appointments, opening hours, or emergency notices.

CURRENT DATE CONTEXT:
Today's date is: {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A, %B %d, %Y')})

DATE INTERPRETATION GUIDELINES:
- "today" = {datetime.now().strftime('%Y-%m-%d')}
- "tomorrow" = {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
- "day after tomorrow" = {(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')}
- "next Monday/Tuesday/etc" = calculate the next occurrence of that weekday
- Always convert dates to YYYY-MM-DD format when calling the appointment function
- If patient says relative dates like "tomorrow" or "next week", convert to exact dates

APPOINTMENT BOOKING PROCESS:
1. Collect patient name
2. Collect phone number
3. Collect email address and confirm spelling
4. Collect preferred date/time - ALWAYS convert relative dates to YYYY-MM-DD format
5. Assign doctor and department based on their needs
6. After collecting ALL information, confirm the appointment and automatically send confirmation email AND add to hospital calendar by calling the send_appointment_email function

CRITICAL: When you have all appointment details (name, email, phone, date, time, doctor, department), immediately call the send_appointment_email function to send the confirmation email AND add to hospital calendar. Then tell the patient: "Perfect! Your appointment is confirmed. I've sent you a confirmation email and added it to our hospital calendar."

You have access to the following function:
- send_appointment_email: Use this to send appointment confirmation emails AND add appointments to hospital calendar with all collected details

[Voice & Persona]
Personality:
• Friendly, calming, competent.
• Warm, understanding, authentic.
• Shows real interest in the patient's request.
• Confident but humble if something is unknown.
• Numbers are spoken in words. E.g. 6 is six or 94 is ninety-four.

Speech style:
• Natural contractions ("we've got", "you can").
• Mix of short and slightly longer sentences.
• Occasional fillers ("hm", "actually") for natural flow.
• Moderate pace, slower for complex info.
• Shortened or incomplete sentences when context is clear ("Monday to Friday, eight to four" instead of "Our opening hours are…").
• No repeating the question unless for clarification.
• No unsolicited extra info like emergency numbers, prices, or promotions.
• Context-based follow-up questions, not rigid scripts.

Keep responses concise and helpful. You are here to assist with hospital-related inquiries and appointment bookings."""
        )

        # Register the appointment email function handler
        llm.register_function("send_appointment_email", handle_send_appointment_email)
        logger.info("=== TWILIO: Email function registered successfully ===")

        # Create context with tools for function calling support
        context = OpenAILLMContext(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Archana, a patient service voice assistant for Renova Hospitals.

Your main role is to answer patient questions briefly, clearly, and politely regarding our services, appointments, opening hours, or emergency notices.

CURRENT DATE CONTEXT:
Today's date is: {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A, %B %d, %Y')})

DATE INTERPRETATION GUIDELINES:
- "today" = {datetime.now().strftime('%Y-%m-%d')}
- "tomorrow" = {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
- "day after tomorrow" = {(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')}
- "next Monday/Tuesday/etc" = calculate the next occurrence of that weekday
- Always convert dates to YYYY-MM-DD format when calling the appointment function
- If patient says relative dates like "tomorrow" or "next week", convert to exact dates

APPOINTMENT BOOKING PROCESS:
1. Collect patient name
2. Collect phone number
3. Collect email address and confirm spelling
4. Collect preferred date/time - ALWAYS convert relative dates to YYYY-MM-DD format
5. Assign doctor and department based on their needs
6. After collecting ALL information, confirm the appointment and automatically send confirmation email AND add to hospital calendar by calling the send_appointment_email function

CRITICAL: When you have all appointment details (name, email, phone, date, time, doctor, department), immediately call the send_appointment_email function to send the confirmation email AND add to hospital calendar. Then tell the patient: "Perfect! Your appointment is confirmed. I've sent you a confirmation email and added it to our hospital calendar."

You have access to the following function:
- send_appointment_email: Use this to send appointment confirmation emails AND add appointments to hospital calendar with all collected details

[Voice & Persona]
Personality:
• Friendly, calming, competent.
• Warm, understanding, authentic.
• Shows real interest in the patient's request.
• Confident but humble if something is unknown.
• Numbers are spoken in words. E.g. 6 is six or 94 is ninety-four.

Speech style:
• Natural contractions ("we've got", "you can").
• Mix of short and slightly longer sentences.
• Occasional fillers ("hm", "actually") for natural flow.
• Moderate pace, slower for complex info.
• Shortened or incomplete sentences when context is clear ("Monday to Friday, eight to four" instead of "Our opening hours are…").
• No repeating the question unless for clarification.
• No unsolicited extra info like emergency numbers, prices, or promotions.
• Context-based follow-up questions, not rigid scripts.

Keep responses concise and helpful. You are here to assist with hospital-related inquiries and appointment bookings."""
                }
            ],
            tools=appointment_tools
        )

        # Create context aggregator for function calling support
        context_aggregator = llm.create_context_aggregator(context)

        # Create pipeline with function calling support
        pipeline = Pipeline([
            transport.input(),              # Audio input from Twilio
            context_aggregator.user(),      # User context aggregation
            llm,                           # Gemini Live processing with function calling
            transport.output(),            # Audio output to Twilio
            context_aggregator.assistant() # Assistant context aggregation
        ])

        logger.info("Starting Pipecat pipeline for Twilio call")

        # Create pipeline parameters and task the way reference implementation does it
        params = PipelineParams(allow_interruptions=True)
        task = PipelineTask(pipeline, params=params)
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)

    except Exception as e:
        logger.error(f"Error in Pipecat bot: {e}")
        raise

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle Twilio Media Stream WebSocket connection with integrated Pipecat."""
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    try:
        # Get the first two messages from Twilio (start and media setup)
        start_data = websocket.iter_text()
        await start_data.__anext__()  # Skip the first message
        call_data = json.loads(await start_data.__anext__())  # Get call data
        logger.info(f"Call data received: {call_data}")

        # Extract stream SID and call SID from call data
        stream_sid = call_data["start"]["streamSid"]
        call_sid = call_data["start"]["callSid"]
        logger.info(f"Starting bot for stream: {stream_sid}, call: {call_sid}")

        # Run the integrated Pipecat bot with both SIDs
        await run_pipecat_bot(websocket, stream_sid, call_sid)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")

@app.get("/twilio/calls")
async def get_active_calls():
    """Get information about active calls."""
    return {
        "active_calls": active_calls,
        "count": len(active_calls)
    }

if __name__ == "__main__":
    # Check required environment variables
    if not TWILIO_ACCOUNT_SID:
        logger.error("TWILIO_ACCOUNT_SID environment variable is required")
        sys.exit(1)

    if not TWILIO_AUTH_TOKEN:
        logger.error("TWILIO_AUTH_TOKEN environment variable is required")
        sys.exit(1)

    if not TWILIO_PHONE_NUMBER:
        logger.error("TWILIO_PHONE_NUMBER environment variable is required")
        sys.exit(1)

    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable is required")
        sys.exit(1)

    logger.info("Starting Integrated Twilio-Pipecat Voice Server")
    logger.info(f"Configure your Twilio phone number webhook to: http://your-domain:{PORT}/twilio/voice")

    # Run the server
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )