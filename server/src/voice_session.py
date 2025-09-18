import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

from pipecat.frames.frames import (
    Frame,
    AudioRawFrame,
    TranscriptionFrame,
    TextFrame,
    EndFrame,
    CancelFrame
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.websocket.server import (
    WebsocketServerParams,
    WebsocketServerTransport
)

import google.generativeai as genai

import structlog

logger = structlog.get_logger(__name__)


class VoiceSession:
    """Manages individual voice agent sessions with Pipecat SmallWebRTC integration."""

    def __init__(
        self,
        session_id: str,
        websocket_handler,
        gemini_api_key: str,
        system_prompt: str = None,
        session_timeout: int = 1800  # 30 minutes
    ):
        self.session_id = session_id
        self.websocket_handler = websocket_handler
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.session_timeout = session_timeout
        self.is_active = False
        self.is_ending = False

        # AI service configuration
        self.gemini_api_key = gemini_api_key
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Pipeline components
        self.pipeline: Optional[Pipeline] = None
        self.pipeline_task: Optional[PipelineTask] = None
        self.runner: Optional[PipelineRunner] = None
        self.transport: Optional[WebsocketServerTransport] = None

        # WebRTC state
        self.webrtc_ready = False
        self.peer_connection = None

        # Gemini Live session
        self.gemini_session = None

        # Metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "audio_frames_processed": 0,
            "gemini_responses_count": 0,
            "errors_count": 0
        }

    def _default_system_prompt(self) -> str:
        """Default system prompt for the voice agent."""
        return """You are a helpful AI voice assistant. You should:
        1. Respond naturally and conversationally
        2. Keep responses concise but informative
        3. Be friendly and professional
        4. Ask clarifying questions when needed
        5. Acknowledge when you don't know something

        Remember you're in a voice conversation, so avoid complex formatting or long lists."""

    async def initialize(self) -> bool:
        """Initialize the voice session with Gemini Live."""
        try:
            logger.info("Initializing voice session with Gemini Live", session_id=self.session_id)

            # Configure Gemini API
            genai.configure(api_key=self.gemini_api_key)

            # Create Gemini Live service
            gemini_service = GoogleLLMService(
                api_key=self.gemini_api_key,
                model="gemini-2.0-flash-exp",
                enable_live_api=True,
                system_instruction=self.system_prompt
            )

            # Create LLM context with system prompt
            context = LLMContext(
                messages=[
                    {"role": "system", "content": self.system_prompt}
                ]
            )

            # Create VAD analyzer (temporarily disabled)
            # vad = SileroVADAnalyzer()

            # Create transport for WebRTC with Gemini Live audio handling
            transport_params = WebsocketServerParams(
                audio_out_enabled=True,
                audio_in_enabled=True,
                add_wav_header=False,
                vad_enabled=False,  # Disabled VAD for now
                # vad_analyzer=vad,
                vad_audio_passthrough=True,
                audio_out_sample_rate=24000,  # Gemini Live preferred sample rate
                audio_in_sample_rate=24000
            )

            self.transport = WebsocketServerTransport(transport_params)

            # Create pipeline with Gemini Live (handles STT, LLM, and TTS internally)
            self.pipeline = Pipeline([
                self.transport.input(),   # Audio input from WebRTC
                gemini_service,           # Gemini Live (STT + LLM + TTS)
                self.transport.output()   # Audio output to WebRTC
            ])

            # Create pipeline task and runner
            self.pipeline_task = PipelineTask(
                self.pipeline,
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True
            )

            self.runner = PipelineRunner()

            logger.info("Voice session initialized successfully with Gemini Live", session_id=self.session_id)
            return True

        except Exception as e:
            logger.error("Failed to initialize voice session with Gemini Live",
                        session_id=self.session_id, error=str(e))
            self.metrics["errors_count"] += 1
            return False

    async def start(self) -> bool:
        """Start the voice session pipeline."""
        try:
            if not self.pipeline or not self.pipeline_task:
                logger.error("Pipeline not initialized", session_id=self.session_id)
                return False

            logger.info("Starting voice session", session_id=self.session_id)

            # Start the pipeline
            await self.runner.run(self.pipeline_task)

            self.is_active = True
            self.last_activity = datetime.utcnow()

            logger.info("Voice session started successfully", session_id=self.session_id)
            return True

        except Exception as e:
            logger.error("Failed to start voice session",
                        session_id=self.session_id, error=str(e))
            self.metrics["errors_count"] += 1
            return False

    async def handle_webrtc_offer(self, offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle WebRTC offer and return answer."""
        try:
            logger.info("Handling WebRTC offer", session_id=self.session_id)

            if not self.transport:
                logger.error("Transport not initialized", session_id=self.session_id)
                return None

            # Process the offer through the transport
            answer = await self.transport.handle_offer(offer)

            if answer:
                self.webrtc_ready = True
                self.last_activity = datetime.utcnow()
                logger.info("WebRTC offer processed successfully", session_id=self.session_id)
                return answer
            else:
                logger.error("Failed to process WebRTC offer", session_id=self.session_id)
                return None

        except Exception as e:
            logger.error("Error handling WebRTC offer",
                        session_id=self.session_id, error=str(e))
            self.metrics["errors_count"] += 1
            return None

    async def handle_webrtc_answer(self, answer: Dict[str, Any]) -> bool:
        """Handle WebRTC answer."""
        try:
            logger.info("Handling WebRTC answer", session_id=self.session_id)

            if not self.transport:
                logger.error("Transport not initialized", session_id=self.session_id)
                return False

            success = await self.transport.handle_answer(answer)

            if success:
                self.webrtc_ready = True
                self.last_activity = datetime.utcnow()
                logger.info("WebRTC answer processed successfully", session_id=self.session_id)
            else:
                logger.error("Failed to process WebRTC answer", session_id=self.session_id)

            return success

        except Exception as e:
            logger.error("Error handling WebRTC answer",
                        session_id=self.session_id, error=str(e))
            self.metrics["errors_count"] += 1
            return False

    async def handle_ice_candidate(self, candidate: Dict[str, Any]) -> bool:
        """Handle ICE candidate."""
        try:
            if not self.transport:
                return False

            success = await self.transport.handle_ice_candidate(candidate)

            if success:
                self.last_activity = datetime.utcnow()

            return success

        except Exception as e:
            logger.error("Error handling ICE candidate",
                        session_id=self.session_id, error=str(e))
            self.metrics["errors_count"] += 1
            return False

    async def send_audio_frame(self, audio_data: bytes) -> bool:
        """Send audio frame to the pipeline."""
        try:
            if not self.pipeline or not self.is_active:
                return False

            # Create audio frame
            frame = AudioRawFrame(
                audio=audio_data,
                sample_rate=16000,
                num_channels=1
            )

            # Send to pipeline
            await self.pipeline.queue_frame(frame)

            self.metrics["audio_frames_processed"] += 1
            self.last_activity = datetime.utcnow()

            return True

        except Exception as e:
            logger.error("Error sending audio frame",
                        session_id=self.session_id, error=str(e))
            self.metrics["errors_count"] += 1
            return False

    async def end_session(self) -> None:
        """End the voice session and cleanup resources."""
        if self.is_ending:
            return

        self.is_ending = True

        try:
            logger.info("Ending voice session", session_id=self.session_id)

            # Send end frame to pipeline
            if self.pipeline and self.is_active:
                await self.pipeline.queue_frame(EndFrame())

            # Stop pipeline
            if self.runner and self.pipeline_task:
                await self.runner.stop()

            # Close transport
            if self.transport:
                await self.transport.cleanup()

            self.is_active = False

            # Log session metrics
            duration = datetime.utcnow() - self.created_at
            logger.info(
                "Voice session ended",
                session_id=self.session_id,
                duration_seconds=duration.total_seconds(),
                metrics=self.metrics
            )

        except Exception as e:
            logger.error("Error ending voice session",
                        session_id=self.session_id, error=str(e))
            self.metrics["errors_count"] += 1

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if not self.is_active:
            return True

        timeout_threshold = datetime.utcnow() - timedelta(seconds=self.session_timeout)
        return self.last_activity < timeout_threshold

    def get_session_info(self) -> Dict[str, Any]:
        """Get session information."""
        duration = datetime.utcnow() - self.created_at
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "is_active": self.is_active,
            "webrtc_ready": self.webrtc_ready,
            "metrics": self.metrics.copy()
        }

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()