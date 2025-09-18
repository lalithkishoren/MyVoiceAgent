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

# Import Gmail email functionality
from gmail_routes import router as gmail_router
from appointment_functions import appointment_tools, handle_send_appointment_email

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Pipecat server with proper transport")
    yield
    logger.info("Shutting down Pipecat server")

# FastAPI app
app = FastAPI(
    title="Pipecat Voice Server with Proper Transport",
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

# Include Gmail routes
app.include_router(gmail_router)

async def run_bot(websocket: WebSocket, session_id: str, voice_id: str = "Charon"):
    """Run a Pipecat bot using proper FastAPI WebSocket transport."""
    try:
        # Create FastAPI WebSocket transport with high quality audio settings
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_analyzer=SileroVADAnalyzer(),
                serializer=ProtobufFrameSerializer(),
                # High quality audio settings
                audio_out_sample_rate=24000,  # Higher sample rate for better quality
                audio_in_sample_rate=16000,
                audio_out_channels=1,
            )
        )

        # Initialize Gemini Multimodal Live service with selected voice and function calling
        llm = GeminiMultimodalLiveLLMService(
            api_key=os.getenv("GEMINI_API_KEY"),
            voice_id=voice_id,  # Configurable voice: Puck, Charon, Kore, Fenrir
            model="models/gemini-2.0-flash-exp",  # Use latest model
            tools=appointment_tools,  # Add appointment function tools
            # System instruction for natural conversation and greeting
            system_instruction=f"""You are Archana, a patient service voice assistant for Renova Hospitals.

Your main role is to answer patient questions briefly, clearly, and politely regarding our services, appointments, opening hours, or emergency notices.

IMPORTANT: Always respond in ENGLISH only.

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

Start every conversation with: "Hi! How are you? I'm Archana, your AI assistant from Renova Hospitals. How can I help you today?"

Speak naturally with contractions and natural rhythm."""
        )

        # Register the appointment email function handler
        llm.register_function("send_appointment_email", handle_send_appointment_email)

        # Create context with tools for function calling support
        context = OpenAILLMContext(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Archana, a patient service voice assistant for Renova Hospitals.

Your main role is to answer patient questions briefly, clearly, and politely regarding our services, appointments, opening hours, or emergency notices.

IMPORTANT: Always respond in ENGLISH only.

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

Start every conversation with: "Hi! How are you? I'm Archana, your AI assistant from Renova Hospitals. How can I help you today?"

Speak naturally with contractions and natural rhythm."""
                }
            ],
            tools=appointment_tools
        )

        # Create context aggregator for function calling support
        context_aggregator = llm.create_context_aggregator(context)

        # Create pipeline using RECOMMENDED PATTERN for Gemini Live with function calling
        pipeline = Pipeline([
            transport.input(),              # Audio input from client
            context_aggregator.user(),      # User context aggregation
            llm,                           # Gemini Multimodal Live processing (handles STT + LLM + TTS + Function Calling)
            transport.output(),            # Audio output to client
            context_aggregator.assistant() # Assistant context aggregation
        ])

        # Create task
        task = PipelineTask(
            pipeline,
            idle_timeout_secs=30
        )

        # Event handlers
        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"Client connected: {session_id}")
            # Start with initial LLM run to trigger greeting
            await task.queue_frames([LLMRunFrame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info(f"Client disconnected: {session_id}")
            await task.cancel()

        # Store session
        active_sessions[session_id] = task

        # Run pipeline with Windows-compatible runner
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)

    except Exception as e:
        logger.error(f"Bot error for session {session_id}: {e}")
    finally:
        # Cleanup session
        if session_id in active_sessions:
            del active_sessions[session_id]

@app.get("/")
async def root():
    """Root endpoint."""
    print("Root endpoint accessed!")  # Debug log
    return {
        "message": "Pipecat Voice Server with Gmail Integration",
        "websocket_url": "ws://localhost:8090/ws",
        "status": "running",
        "active_sessions": len(active_sessions),
        "gmail_enabled": True
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "websocket_endpoint": "ws://localhost:8090/ws"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, voice_id: str = "Charon"):
    """WebSocket endpoint using proper Pipecat transport."""
    print(f"=== WEBSOCKET LOG: Connection attempt received ===")
    print(f"=== WEBSOCKET LOG: Voice ID: {voice_id} ===")

    try:
        await websocket.accept()
        print(f"=== WEBSOCKET LOG: WebSocket accepted ===")
    except Exception as e:
        print(f"=== WEBSOCKET ERROR: Failed to accept: {e} ===")
        return

    # Generate session ID
    session_id = f"session-{len(active_sessions) + 1}"
    print(f"=== WEBSOCKET LOG: Session ID generated: {session_id} ===")
    logger.info(f"WebSocket connection accepted: {session_id} with voice: {voice_id}")

    try:
        # Run the bot using RECOMMENDED Pipecat pattern
        await run_bot(websocket, session_id, voice_id)

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        logger.info(f"WebSocket connection closed: {session_id}")

if __name__ == "__main__":
    # Check required environment variables
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is required")
        sys.exit(1)

    logger.info("Starting Pipecat server with proper transport pattern")
    logger.info("Using FastAPIWebsocketTransport as recommended in documentation")

    # Run the server
    uvicorn.run(
        app,
        host="127.0.0.1",  # Force IPv4 instead of localhost
        port=8091,
        log_level="info"
    )