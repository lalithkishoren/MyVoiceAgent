#!/usr/bin/env python3

import os
import sys
import json
import base64
import asyncio
import websockets
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
import structlog

# Twilio imports
from twilio.twiml.voice_response import VoiceResponse, Stream, Connect
from twilio.rest import Client

# Audio bridge import
from audio_bridge import TwilioAudioBridge, PipecatTwilioConnector

# Load environment variables
load_dotenv()

# Configure logging
logger = structlog.get_logger(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("TWILIO_PORT", "8091"))

# Global variables
active_calls = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Twilio Voice Server")
    logger.info(f"Twilio Phone Number: {TWILIO_PHONE_NUMBER}")
    logger.info(f"Server running on {HOST}:{PORT}")
    yield
    logger.info("Shutting down Twilio Voice Server")

# FastAPI app
app = FastAPI(
    title="Twilio Voice Integration Server",
    description="Handles Twilio webhooks and media streams for phone integration",
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
        "message": "Twilio Voice Integration Server",
        "status": "running",
        "phone_number": TWILIO_PHONE_NUMBER,
        "webhook_url": f"http://{HOST}:{PORT}/twilio/voice",
        "stream_url": f"ws://{HOST}:{PORT}/twilio/stream",
        "active_calls": len(active_calls)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "twilio-integration",
        "active_calls": len(active_calls),
        "twilio_configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)
    }

@app.post("/twilio/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio voice calls with webhook."""
    try:
        # Get form data from Twilio webhook
        form_data = await request.form()

        # Extract call information
        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        call_status = form_data.get("CallStatus")

        logger.info(f"Incoming call: {call_sid} from {from_number} to {to_number}, status: {call_status}")

        # Create TwiML response
        response = VoiceResponse()

        # Brief greeting message
        response.say(
            "Hello! Connecting you to our AI assistant.",
            voice="Polly.Joanna"
        )

        # Set up media stream for real-time audio
        # Get public URL from environment (using NGROK_URL for backward compatibility)
        public_url = os.getenv("NGROK_URL") or os.getenv("PUBLIC_URL", "https://renova--codecanyon-landing.us-central1.hosted.app")
        stream_url = f"{public_url.replace('https://', 'wss://')}/twilio/stream"

        logger.info(f"Creating Twilio Stream with URL: {stream_url}")

        # Create Connect element with Stream for bidirectional audio
        connect = Connect()
        stream = Stream(url=stream_url)
        connect.append(stream)
        response.append(connect)

        # Store call information
        active_calls[call_sid] = {
            "from": from_number,
            "to": to_number,
            "status": call_status,
            "timestamp": asyncio.get_event_loop().time()
        }

        logger.info(f"Generated TwiML response for call {call_sid}")

        # Return TwiML response
        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")

        # Fallback TwiML response
        response = VoiceResponse()
        response.say("Sorry, there was an error processing your call. Please try again later.")

        return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/status")
async def handle_call_status(request: Request):
    """Handle call status updates from Twilio."""
    try:
        form_data = await request.form()

        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")

        logger.info(f"Call status update: {call_sid} - {call_status}")

        # Update call status
        if call_sid in active_calls:
            active_calls[call_sid]["status"] = call_status

            # Clean up completed calls
            if call_status in ["completed", "failed", "busy", "no-answer"]:
                logger.info(f"Cleaning up call {call_sid}")
                del active_calls[call_sid]

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error handling call status: {e}")
        return {"status": "error", "message": str(e)}

@app.websocket("/twilio/stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle Twilio Media Stream WebSocket connection with proper message handling."""
    logger.info(f"WebSocket connection attempt from {websocket.client}")
    await websocket.accept()
    logger.info("Media stream WebSocket connection established and accepted")

    # Create Pipecat-Twilio connector
    connector = PipecatTwilioConnector()

    try:
        # Handle incoming messages from Twilio
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                event = data.get("event")

                logger.info(f"Received Twilio event: {event}")

                if event == "connected":
                    logger.info("Twilio Media Stream connected")

                elif event == "start":
                    logger.info(f"Media stream started: {data}")
                    stream_sid = data.get("streamSid")

                    # Set up the connector with WebSocket and stream ID
                    connector.set_twilio_websocket(websocket, stream_sid)

                    # Connect to Pipecat when stream starts
                    await connector.connect_to_pipecat()

                elif event == "media":
                    # Process incoming audio through simple TTS response
                    payload = data["media"]["payload"]
                    logger.debug(f"Received audio payload of length: {len(payload)}")

                    # For now, send a simple TTS response instead of full Pipecat
                    # This proves the pipeline works before full integration

                    # Generate simple response audio (we'll use echo for now)
                    # TODO: Replace with actual Gemini Live TTS
                    response_payload = payload  # Echo back

                    media_response = {
                        "event": "media",
                        "streamSid": data.get("streamSid"),
                        "media": {
                            "payload": response_payload
                        }
                    }

                    await websocket.send_text(json.dumps(media_response))
                    logger.debug("Sent audio response back to Twilio")

                elif event == "stop":
                    logger.info("Media stream stopped")
                    break

                else:
                    logger.warning(f"Unknown Twilio event: {event}")

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Twilio message: {e}")
            except Exception as e:
                logger.error(f"Error handling Twilio message: {e}")

    except Exception as e:
        logger.error(f"Media stream error: {e}")
    finally:
        logger.info("Media stream WebSocket connection closed")

@app.get("/twilio/calls")
async def get_active_calls():
    """Get information about active calls."""
    return {
        "active_calls": active_calls,
        "count": len(active_calls)
    }

@app.get("/test-websocket")
async def test_websocket_endpoint():
    """Test endpoint to verify WebSocket is accessible."""
    return {"message": "WebSocket endpoint is accessible", "url": "/twilio/stream"}

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

    logger.info("Starting Twilio Voice Integration Server")
    logger.info(f"Configure your Twilio phone number webhook to: http://your-domain:{PORT}/twilio/voice")

    # Run the server
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )