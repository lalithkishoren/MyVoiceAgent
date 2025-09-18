#!/usr/bin/env python3

import asyncio
import json
import os
import sys
import platform
import base64
import io
import wave
import struct
from contextlib import asynccontextmanager
from typing import Dict, Any

# Google APIs for speech processing
import google.generativeai as genai
from google.cloud import speech
from google.cloud import texttospeech

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.websocket.server import WebsocketServerTransport, WebsocketServerParams
from pipecat.frames.frames import TextFrame

import structlog

# Load environment variables
load_dotenv()

# Configure logging
logger = structlog.get_logger(__name__)

# Initialize Google APIs
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Google Cloud clients with error handling
try:
    speech_client = speech.SpeechClient()
    logger.info("Google Cloud Speech-to-Text client initialized")
except Exception as e:
    logger.warning(f"Google Cloud Speech-to-Text not available: {e}")
    speech_client = None

try:
    tts_client = texttospeech.TextToSpeechClient()
    logger.info("Google Cloud Text-to-Speech client initialized")
except Exception as e:
    logger.warning(f"Google Cloud Text-to-Speech not available: {e}")
    tts_client = None

class WindowsCompatibleBot:
    """Windows-compatible Pipecat bot that avoids PipelineRunner signal issues."""

    def __init__(self):
        self.task = None
        self.pipeline = None
        self.transport = None
        self.runner = None
        self.running = False

    async def start(self):
        """Start the bot pipeline with Windows-compatible approach."""
        try:
            # Initialize Google LLM service
            llm = GoogleLLMService(
                api_key=os.getenv("GEMINI_API_KEY"),
                model="gemini-1.5-flash"
            )

            # Create WebSocket transport
            self.transport = WebsocketServerTransport(
                params=WebsocketServerParams(
                    host="0.0.0.0",
                    port=8765,  # WebSocket port
                    audio_out_enabled=True,
                    audio_in_enabled=True,
                )
            )

            # Create pipeline
            self.pipeline = Pipeline([
                self.transport.input(),
                llm,
                self.transport.output()
            ])

            # Create task with idle timeout
            self.task = PipelineTask(
                self.pipeline,
                idle_timeout_secs=30
            )

            # Use PipelineRunner but disable signal handling for Windows
            from pipecat.pipeline.runner import PipelineRunner
            self.runner = PipelineRunner(handle_sigint=False)

            # Start the runner (Windows-compatible)
            self.running = True
            await self.runner.run(self.task)

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self.running = False
            raise

    async def stop(self):
        """Stop the bot."""
        self.running = False
        if self.runner:
            await self.runner.stop()
        if self.task:
            await self.task.stop()

# Global bot instance
bot_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    global bot_instance

    # Startup
    try:
        bot_instance = WindowsCompatibleBot()
        # Start bot in background task
        asyncio.create_task(bot_instance.start())
        logger.info("Windows-compatible bot started successfully")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

    yield

    # Shutdown
    if bot_instance:
        await bot_instance.stop()
        logger.info("Bot stopped")

# FastAPI app with lifespan
app = FastAPI(
    title="Windows-Compatible Pipecat Voice Server",
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
    """Root endpoint."""
    return {
        "message": "Windows-Compatible Pipecat Voice Server",
        "platform": platform.system(),
        "websocket_url": "ws://localhost:8765",
        "signaling_url": "ws://localhost:8080/ws",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global bot_instance
    return {
        "status": "healthy",
        "platform": platform.system(),
        "bot_running": bot_instance is not None and bot_instance.running,
        "websocket_transport": "ws://localhost:8765",
        "signaling_endpoint": "ws://localhost:8080/ws"
    }

@app.post("/start-session")
async def start_session():
    """Start a new voice session."""
    try:
        return {
            "websocket_url": "ws://localhost:8765",
            "signaling_url": "ws://localhost:8080/ws",
            "session_id": "windows-session",
            "status": "ready",
            "platform": platform.system()
        }
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_simple_audio_response(text):
    """Generate a simple audio response (sine wave beep pattern for now)."""
    import math

    # Simple beep pattern to simulate TTS response
    sample_rate = 16000
    duration = 1.0  # 1 second
    frequency = 440  # A4 note

    samples = int(sample_rate * duration)
    audio_data = []

    for i in range(samples):
        # Generate sine wave
        value = math.sin(2 * math.pi * frequency * i / sample_rate)
        # Convert to 16-bit integer
        audio_data.append(int(value * 16000))

    return audio_data

def pcm_to_wav_bytes(pcm_data, sample_rate=16000):
    """Convert PCM data to WAV format bytes."""
    # Convert PCM array to bytes
    pcm_bytes = struct.pack('<' + 'h' * len(pcm_data), *pcm_data)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)

    return wav_buffer.getvalue()

async def speech_to_text(audio_data, sample_rate=16000):
    """Convert audio data to text using Google Speech-to-Text."""
    if not speech_client:
        logger.warning("Speech-to-Text client not available, using fallback")
        return "Hello, I can hear you but speech recognition is not configured."

    try:
        # Convert PCM array to WAV bytes
        wav_bytes = pcm_to_wav_bytes(audio_data, sample_rate)

        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
        )

        audio = speech.RecognitionAudio(content=wav_bytes)

        # Perform the transcription
        response = speech_client.recognize(config=config, audio=audio)

        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            logger.info(f"Speech-to-text result: {transcript}")
            return transcript
        else:
            logger.warning("No speech detected in audio")
            return ""

    except Exception as e:
        logger.error(f"Speech-to-text error: {e}")
        return ""

async def generate_llm_response(user_text):
    """Generate response using Gemini LLM."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""You are a helpful voice assistant.
        User said: "{user_text}"

        Respond in a conversational, friendly way. Keep your response brief (1-2 sentences) since this is a voice conversation."""

        response = model.generate_content(prompt)
        ai_response = response.text

        logger.info(f"LLM response: {ai_response}")
        return ai_response

    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return "I'm sorry, I didn't understand that. Could you please try again?"

async def text_to_speech(text):
    """Convert text to speech using Google Text-to-Speech."""
    if not tts_client:
        logger.warning("Text-to-Speech client not available, using fallback")
        return generate_simple_audio_response(text)

    try:
        # Set up the text input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F",  # Pleasant female voice
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        # Configure audio
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000
        )

        # Generate speech
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Convert audio bytes to PCM array
        audio_data = []
        audio_bytes = response.audio_content

        # Skip WAV header (first 44 bytes) and convert to 16-bit integers
        pcm_bytes = audio_bytes[44:]  # Skip WAV header
        for i in range(0, len(pcm_bytes), 2):
            if i + 1 < len(pcm_bytes):
                sample = struct.unpack('<h', pcm_bytes[i:i+2])[0]
                audio_data.append(sample)

        logger.info(f"Generated TTS audio with {len(audio_data)} samples")
        return audio_data

    except Exception as e:
        logger.error(f"Text-to-speech error: {e}")
        # Fallback to simple beep
        return generate_simple_audio_response(text)

def generate_simple_melody_response():
    """Generate a simple melody as fallback."""
    import math

    sample_rate = 16000
    audio_data = []

    # Create a pleasant welcome melody: C4-E4-G4-C5
    frequencies = [261.63, 329.63, 392.00, 523.25]  # C-E-G-C chord
    note_duration = 0.3  # Each note plays for 0.3 seconds

    for frequency in frequencies:
        samples = int(sample_rate * note_duration)

        for i in range(samples):
            # Generate sine wave with fade-in/fade-out
            progress = i / samples
            fade = min(progress * 4, (1 - progress) * 4, 1)  # Smooth fade

            value = math.sin(2 * math.pi * frequency * i / sample_rate) * fade
            # Convert to 16-bit integer with lower volume for pleasantness
            audio_data.append(int(value * 8000))  # Half volume of simple response

    # Add a brief pause
    pause_samples = int(sample_rate * 0.2)
    audio_data.extend([0] * pause_samples)

    return audio_data

def generate_welcome_audio_response(text):
    """Generate a welcome audio response using TTS."""
    import asyncio

    # Run TTS in event loop
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(text_to_speech(text))
    except Exception as e:
        logger.error(f"Welcome TTS error: {e}")
        # Fallback to melody
        return generate_simple_melody_response()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket signaling endpoint for frontend compatibility."""
    await websocket.accept()
    logger.info("WebSocket connection established on /ws")

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "start-session":
                    # Handle session start with WebRTC offer
                    offer = message.get("offer")
                    if offer:
                        session_id = "pipecat-session"

                        # Send session-created response
                        response = {
                            "type": "session-created",
                            "sessionId": session_id,
                            "timestamp": asyncio.get_event_loop().time(),
                            "websocket_url": "ws://localhost:8765"
                        }
                        await websocket.send_text(json.dumps(response))
                        logger.info("Session created, client should connect to Pipecat transport")

                        # Send welcome voice message after a short delay
                        await asyncio.sleep(1)  # Give frontend time to set up audio
                        welcome_message = "Hi! How are you? I'm ready to chat with you."
                        welcome_audio = await text_to_speech(welcome_message)
                        welcome_response = {
                            "type": "audio-response",
                            "sessionId": session_id,
                            "text": welcome_message,
                            "audio": welcome_audio,
                            "sampleRate": 16000
                        }
                        await websocket.send_text(json.dumps(welcome_response))
                        logger.info(f"Sent welcome message: {welcome_message}")

                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "No offer provided"
                        }))

                elif message_type == "offer":
                    # Handle WebRTC offer
                    response = {
                        "type": "answer",
                        "answer": {"type": "answer", "sdp": "placeholder-answer"},
                        "sessionId": message.get("sessionId", "pipecat-session")
                    }
                    await websocket.send_text(json.dumps(response))

                elif message_type == "ice-candidate":
                    # Handle ICE candidates (acknowledge)
                    response = {
                        "type": "ice-candidate-received",
                        "sessionId": message.get("sessionId", "pipecat-session")
                    }
                    await websocket.send_text(json.dumps(response))

                elif message_type == "audio-data":
                    # Handle incoming audio data with full AI pipeline
                    audio_array = message.get("audio", [])
                    sample_rate = message.get("sampleRate", 16000)
                    session_id = message.get("sessionId")

                    if audio_array and len(audio_array) > 1000:  # Only process if enough audio
                        try:
                            # Step 1: Speech-to-Text
                            user_text = await speech_to_text(audio_array, sample_rate)

                            if user_text.strip():
                                # Step 2: Generate LLM response
                                ai_text = await generate_llm_response(user_text)

                                # Step 3: Text-to-Speech
                                ai_audio = await text_to_speech(ai_text)

                                # Send back the AI response
                                response = {
                                    "type": "audio-response",
                                    "sessionId": session_id,
                                    "text": ai_text,
                                    "transcript": user_text,
                                    "audio": ai_audio,
                                    "sampleRate": 16000
                                }
                                await websocket.send_text(json.dumps(response))
                                logger.info(f"Processed: '{user_text}' -> '{ai_text}'")

                            else:
                                logger.info("No speech detected in audio, skipping response")

                        except Exception as e:
                            logger.error(f"Error processing audio: {e}")
                            # Send error response
                            error_response = {
                                "type": "audio-response",
                                "sessionId": session_id,
                                "text": "I'm sorry, I didn't understand that.",
                                "audio": await text_to_speech("I'm sorry, I didn't understand that."),
                                "sampleRate": 16000
                            }
                            await websocket.send_text(json.dumps(error_response))

                elif message_type == "ping":
                    # Handle ping
                    await websocket.send_text(json.dumps({"type": "pong"}))

                else:
                    # Unknown message type
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    # Check required environment variables
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is required")
        sys.exit(1)

    # Note: Google Cloud credentials should be set via GOOGLE_APPLICATION_CREDENTIALS
    # or default application credentials for Speech-to-Text and Text-to-Speech

    logger.info(f"Starting server on {platform.system()}")
    logger.info("Google AI services:")
    logger.info("  - Gemini LLM: Using GEMINI_API_KEY")

    if speech_client:
        logger.info("  - Speech-to-Text: ✅ Available")
    else:
        logger.info("  - Speech-to-Text: ❌ Not configured (using fallback)")

    if tts_client:
        logger.info("  - Text-to-Speech: ✅ Available")
    else:
        logger.info("  - Text-to-Speech: ❌ Not configured (using fallback)")

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )