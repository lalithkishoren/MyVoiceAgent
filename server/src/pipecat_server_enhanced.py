#!/usr/bin/env python3

import asyncio
import os
import sys
import json
from contextlib import asynccontextmanager

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

# Load environment variables
load_dotenv()

# Configure logging
logger = structlog.get_logger(__name__)

# Global variables
active_sessions = {}

# Import Gmail routes
from gmail_routes import router as gmail_router
from enhanced_system_prompt import ENHANCED_SYSTEM_INSTRUCTION
from appointment_email_handler import get_appointment_email_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Enhanced Pipecat server with Gmail integration")
    yield
    logger.info("Shutting down Enhanced Pipecat server")

# FastAPI app
app = FastAPI(
    title="Enhanced Pipecat Voice Server with Gmail Integration",
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
    """Run a Pipecat bot with Gmail integration."""
    try:
        # Initialize appointment email handler
        email_handler = get_appointment_email_handler()

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

        # Initialize Gemini Multimodal Live service with selected voice
        llm = GeminiMultimodalLiveLLMService(
            api_key=os.getenv("GEMINI_API_KEY"),
            voice_id=voice_id,  # Configurable voice: Puck, Charon, Kore, Fenrir
            model="models/gemini-2.0-flash-exp",  # Use latest model
            # Enhanced system instruction with appointment email functionality
            system_instruction=ENHANCED_SYSTEM_INSTRUCTION
        )

        # Create pipeline using RECOMMENDED PATTERN for Gemini Live
        pipeline = Pipeline([
            transport.input(),    # Audio input from client
            llm,                 # Gemini Multimodal Live processing (handles STT + LLM + TTS)
            transport.output(),  # Audio output to client
        ])

        # Create task
        task = PipelineTask(
            pipeline,
            idle_timeout_secs=30
        )

        # Enhanced event handlers with email processing
        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"Client connected: {session_id}")
            active_sessions[session_id] = {
                'status': 'connected',
                'start_time': asyncio.get_event_loop().time(),
                'voice_id': voice_id
            }
            # Start with initial LLM run to trigger greeting
            await task.queue_frames([LLMRunFrame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info(f"Client disconnected: {session_id}")
            if session_id in active_sessions:
                del active_sessions[session_id]

        # Store email handler for potential future use
        # Note: Email processing will be handled through system prompt triggers

        # Store session info
        active_sessions[session_id]['task'] = task
        active_sessions[session_id]['transport'] = transport

        logger.info(f"Starting bot for session {session_id} with voice {voice_id}")

        # Run the pipeline with proper Windows handling
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)

    except Exception as e:
        logger.error(f"Error in voice session {session_id}: {e}")
    finally:
        # Cleanup session
        if session_id in active_sessions:
            del active_sessions[session_id]

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Enhanced Pipecat Voice Server with Gmail Integration",
        "websocket_url": "ws://localhost:8090/ws",
        "status": "running",
        "active_sessions": len(active_sessions),
        "features": [
            "Gemini Live Voice Processing",
            "Gmail Integration",
            "Appointment Confirmation Emails",
            "Voice Command Email Sending",
            "Natural Language Processing"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "websocket_endpoint": "ws://localhost:8090/ws",
        "gmail_integration": "available",
        "voice_processing": "gemini_live"
    }

@app.get("/sessions")
async def get_sessions():
    """Get active sessions information."""
    session_info = {}
    for session_id, session_data in active_sessions.items():
        session_info[session_id] = {
            'status': session_data.get('status', 'unknown'),
            'voice_id': session_data.get('voice_id', 'unknown'),
            'duration': asyncio.get_event_loop().time() - session_data.get('start_time', 0)
        }

    return {
        "total_sessions": len(active_sessions),
        "sessions": session_info
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, voice_id: str = "Charon"):
    """WebSocket endpoint with enhanced Gmail integration."""
    await websocket.accept()

    # Generate session ID
    session_id = f"session-{len(active_sessions) + 1}"
    logger.info(f"WebSocket connection accepted: {session_id} with voice: {voice_id}")

    try:
        # Run the bot with enhanced email functionality
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

    logger.info("Starting Enhanced Pipecat server with Gmail integration")
    logger.info("Features: Voice Processing + Appointment Confirmation Emails")

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8090,  # Use different port to avoid conflict
        log_level="info"
    )