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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Pipecat server with Gmail integration")
    yield
    logger.info("Shutting down Pipecat server")

# FastAPI app
app = FastAPI(
    title="Pipecat Voice Server with Gmail Integration",
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

# Simple system instruction with email collection
SYSTEM_INSTRUCTION = """You are Archana, a patient service voice assistant for Renova Hospitals.

Your main role is to answer patient questions briefly, clearly, and politely regarding our services, appointments, opening hours, or emergency notices.

IMPORTANT: When booking appointments, collect: name, phone number, and EMAIL ADDRESS.

After confirming appointment details, ask: "Could you please provide your email address for the appointment confirmation?"

Always spell-check the email address by reading it back: "I have [email]. Is that correct?"

When appointment is finalized, say: "Perfect! Your appointment is confirmed. I'll send you a confirmation email shortly."

Start every conversation with: "Hi! How are you? I'm Archana, your AI assistant from Renova Hospitals. How can I help you today?"

Speak naturally with contractions and natural rhythm."""

async def run_bot(websocket: WebSocket, session_id: str, voice_id: str = "Charon"):
    """Run a Pipecat bot."""
    try:
        # Create FastAPI WebSocket transport
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_analyzer=SileroVADAnalyzer(),
                serializer=ProtobufFrameSerializer(),
                audio_out_sample_rate=24000,
                audio_in_sample_rate=16000,
                audio_out_channels=1,
            )
        )

        # Initialize Gemini service
        llm = GeminiMultimodalLiveLLMService(
            api_key=os.getenv("GEMINI_API_KEY"),
            voice_id=voice_id,
            model="models/gemini-2.0-flash-exp",
            system_instruction=SYSTEM_INSTRUCTION
        )

        # Create pipeline
        pipeline = Pipeline([
            transport.input(),
            llm,
            transport.output(),
        ])

        # Create task
        task = PipelineTask(pipeline, idle_timeout_secs=30)

        # Event handlers
        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"Client connected: {session_id}")
            active_sessions[session_id] = {
                'status': 'connected',
                'start_time': asyncio.get_event_loop().time(),
                'voice_id': voice_id
            }
            await task.queue_frames([LLMRunFrame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info(f"Client disconnected: {session_id}")
            if session_id in active_sessions:
                del active_sessions[session_id]

        logger.info(f"Starting bot for session {session_id} with voice {voice_id}")

        # Run pipeline
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)

    except Exception as e:
        logger.error(f"Error in voice session {session_id}: {e}")
    finally:
        if session_id in active_sessions:
            del active_sessions[session_id]

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Pipecat Voice Server with Gmail Integration",
        "websocket_url": "ws://localhost:8090/ws",
        "status": "running",
        "active_sessions": len(active_sessions),
        "gmail_integration": "available"
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
    """WebSocket endpoint."""
    await websocket.accept()

    session_id = f"session-{len(active_sessions) + 1}"
    logger.info(f"WebSocket connection accepted: {session_id} with voice: {voice_id}")

    try:
        await run_bot(websocket, session_id, voice_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        logger.info(f"WebSocket connection closed: {session_id}")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is required")
        sys.exit(1)

    logger.info("Starting Pipecat server with Gmail integration")

    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")