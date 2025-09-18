#!/usr/bin/env python3

import asyncio
import os
import sys
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.websocket.server import WebsocketServerTransport, WebsocketServerParams
from pipecat.frames.frames import TextFrame

import structlog

# Load environment variables
load_dotenv()

# Configure logging
logger = structlog.get_logger(__name__)

class SimplePipecatBot:
    """Simplified Pipecat bot for voice chat."""

    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.task = None
        self.runner = None

    async def start(self):
        """Start the bot pipeline."""
        try:
            # Initialize Google LLM service
            llm = GoogleLLMService(
                api_key=os.getenv("GEMINI_API_KEY"),
                model="gemini-1.5-flash"
            )

            # Create WebSocket transport
            transport = WebsocketServerTransport(
                params=WebsocketServerParams(
                    host="0.0.0.0",
                    port=8765,  # Different port for WebSocket
                    audio_out_enabled=True,
                    audio_in_enabled=True,
                )
            )

            # Create pipeline
            pipeline = Pipeline([
                transport.input(),
                llm,
                transport.output()
            ])

            # Create task with idle timeout
            self.task = PipelineTask(
                pipeline,
                idle_timeout_secs=30
            )
            # Use PipelineRunner but disable signal handling for Windows
            self.runner = PipelineRunner(handle_sigint=False)

            # Start the runner (Windows-compatible)
            await self.runner.run(self.task)

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

# FastAPI app for HTTP endpoints
app = FastAPI(title="Simple Pipecat Voice Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
bot_instance = None

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup."""
    global bot_instance
    try:
        bot_instance = SimplePipecatBot("ws://localhost:8765")
        # Start bot in background
        asyncio.create_task(bot_instance.start())
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Simple Pipecat Voice Server",
        "websocket_url": "ws://localhost:8765",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "bot_running": bot_instance is not None
    }

@app.post("/start-session")
async def start_session():
    """Start a new voice session."""
    try:
        # In a real implementation, you'd create a new bot instance
        # For now, just return connection info
        return {
            "websocket_url": "ws://localhost:8765",
            "session_id": "simple-session",
            "status": "ready"
        }
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Check required environment variables
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is required")
        sys.exit(1)

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )