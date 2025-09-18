#!/usr/bin/env python3

import asyncio
import base64
import json
import struct
import audioop
from typing import Optional, Callable
import websockets
import structlog

logger = structlog.get_logger(__name__)

class TwilioAudioBridge:
    """
    Audio bridge for converting between Twilio Media Stream format and Pipecat format.

    Twilio Audio Format:
    - Encoding: mulaw (8-bit)
    - Sample Rate: 8kHz
    - Channels: 1 (mono)
    - Format: Base64 encoded payload

    Pipecat Audio Format:
    - Encoding: PCM (16-bit)
    - Sample Rate: 16kHz or 24kHz
    - Channels: 1 (mono)
    - Format: Raw bytes
    """

    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate
        self.twilio_sample_rate = 8000
        self.is_active = False

        # Audio processing callbacks
        self.on_audio_from_twilio: Optional[Callable[[bytes], None]] = None
        self.on_audio_to_twilio: Optional[Callable[[bytes], None]] = None

        logger.info(f"Audio bridge initialized: {self.twilio_sample_rate}Hz -> {self.target_sample_rate}Hz")

    def mulaw_to_pcm(self, mulaw_data: bytes) -> bytes:
        """Convert mulaw audio data to 16-bit PCM."""
        try:
            # Convert mulaw to linear PCM
            pcm_data = audioop.ulaw2lin(mulaw_data, 2)  # 2 bytes per sample (16-bit)
            return pcm_data
        except Exception as e:
            logger.error(f"Error converting mulaw to PCM: {e}")
            return b''

    def pcm_to_mulaw(self, pcm_data: bytes) -> bytes:
        """Convert 16-bit PCM audio data to mulaw."""
        try:
            # Convert linear PCM to mulaw
            mulaw_data = audioop.lin2ulaw(pcm_data, 2)  # 2 bytes per sample input
            return mulaw_data
        except Exception as e:
            logger.error(f"Error converting PCM to mulaw: {e}")
            return b''

    def resample_audio(self, audio_data: bytes, from_rate: int, to_rate: int) -> bytes:
        """Resample audio data from one sample rate to another."""
        try:
            if from_rate == to_rate:
                return audio_data

            # Use audioop to change sample rate
            resampled_data = audioop.ratecv(
                audio_data,
                2,  # 2 bytes per sample (16-bit)
                1,  # mono
                from_rate,
                to_rate,
                None  # no state for one-shot conversion
            )[0]

            return resampled_data
        except Exception as e:
            logger.error(f"Error resampling audio {from_rate}Hz -> {to_rate}Hz: {e}")
            return b''

    def process_twilio_audio(self, base64_payload: str) -> bytes:
        """
        Process incoming audio from Twilio Media Stream.
        Converts: mulaw 8kHz -> PCM 16kHz/24kHz
        """
        try:
            # Decode base64 payload
            mulaw_data = base64.b64decode(base64_payload)

            # Convert mulaw to PCM
            pcm_8khz = self.mulaw_to_pcm(mulaw_data)

            # Resample to target rate
            pcm_target = self.resample_audio(
                pcm_8khz,
                self.twilio_sample_rate,
                self.target_sample_rate
            )

            logger.debug(f"Processed Twilio audio: {len(mulaw_data)} mulaw -> {len(pcm_target)} PCM")
            return pcm_target

        except Exception as e:
            logger.error(f"Error processing Twilio audio: {e}")
            return b''

    def process_pipecat_audio(self, pcm_data: bytes) -> str:
        """
        Process outgoing audio to Twilio Media Stream.
        Converts: PCM 16kHz/24kHz -> mulaw 8kHz -> base64
        """
        try:
            # Resample to 8kHz
            pcm_8khz = self.resample_audio(
                pcm_data,
                self.target_sample_rate,
                self.twilio_sample_rate
            )

            # Convert PCM to mulaw
            mulaw_data = self.pcm_to_mulaw(pcm_8khz)

            # Encode as base64
            base64_payload = base64.b64encode(mulaw_data).decode('utf-8')

            logger.debug(f"Processed Pipecat audio: {len(pcm_data)} PCM -> {len(mulaw_data)} mulaw")
            return base64_payload

        except Exception as e:
            logger.error(f"Error processing Pipecat audio: {e}")
            return ''

    async def handle_twilio_message(self, message: str) -> Optional[dict]:
        """Handle incoming message from Twilio Media Stream WebSocket."""
        try:
            data = json.loads(message)

            if data["event"] == "connected":
                logger.info("Twilio Media Stream connected")
                self.is_active = True
                return None

            elif data["event"] == "start":
                logger.info(f"Media stream started: {data}")
                return None

            elif data["event"] == "media":
                # Process incoming audio
                payload = data["media"]["payload"]
                pcm_audio = self.process_twilio_audio(payload)

                # Send to Pipecat pipeline
                if self.on_audio_from_twilio and pcm_audio:
                    self.on_audio_from_twilio(pcm_audio)

                return None

            elif data["event"] == "stop":
                logger.info("Media stream stopped")
                self.is_active = False
                return None

            else:
                logger.warning(f"Unknown Twilio event: {data['event']}")
                return None

        except Exception as e:
            logger.error(f"Error handling Twilio message: {e}")
            return None

    def create_twilio_media_message(self, pcm_audio: bytes) -> dict:
        """Create a Twilio Media Stream message from PCM audio."""
        try:
            base64_payload = self.process_pipecat_audio(pcm_audio)

            if not base64_payload:
                return {}

            return {
                "event": "media",
                "media": {
                    "payload": base64_payload
                }
            }

        except Exception as e:
            logger.error(f"Error creating Twilio media message: {e}")
            return {}

    def set_audio_handlers(self,
                          from_twilio_handler: Callable[[bytes], None],
                          to_twilio_handler: Callable[[bytes], None]):
        """Set callback handlers for audio processing."""
        self.on_audio_from_twilio = from_twilio_handler
        self.on_audio_to_twilio = to_twilio_handler
        logger.info("Audio handlers set for bidirectional processing")

class PipecatTwilioConnector:
    """
    Connector that bridges Pipecat voice pipeline with Twilio Media Streams.
    """

    def __init__(self, pipecat_websocket_url: str = "ws://localhost:8090/ws"):
        self.pipecat_url = pipecat_websocket_url
        self.audio_bridge = TwilioAudioBridge()
        self.pipecat_ws: Optional[websockets.WebSocketServerProtocol] = None
        self.twilio_ws: Optional[websockets.WebSocketServerProtocol] = None
        self.stream_sid: Optional[str] = None

        # Set up audio bridge handlers
        self.audio_bridge.set_audio_handlers(
            self.send_to_pipecat,
            self.send_to_twilio
        )

        logger.info(f"Pipecat-Twilio connector initialized for {pipecat_websocket_url}")

    def set_twilio_websocket(self, websocket, stream_sid: str):
        """Set the Twilio WebSocket connection for sending responses."""
        self.twilio_ws = websocket
        self.stream_sid = stream_sid
        logger.info(f"Twilio WebSocket set for stream {stream_sid}")

    async def connect_to_pipecat(self):
        """Connect to the Sutherland Voice Agent WebSocket."""
        try:
            self.pipecat_ws = await websockets.connect(self.pipecat_url)
            logger.info(f"Connected to Pipecat at {self.pipecat_url}")

            # Start listening for responses from Pipecat
            asyncio.create_task(self._listen_for_pipecat_responses())

            return True
        except Exception as e:
            logger.error(f"Failed to connect to Pipecat: {e}")
            return False

    async def _listen_for_pipecat_responses(self):
        """Listen for audio responses from Pipecat and send them to Twilio."""
        try:
            async for message in self.pipecat_ws:
                try:
                    data = json.loads(message)

                    # Handle audio responses from Pipecat
                    if data.get("type") == "audio":
                        audio_data = base64.b64decode(data["data"])
                        await self.send_to_twilio(audio_data)

                except Exception as e:
                    logger.error(f"Error processing Pipecat response: {e}")

        except Exception as e:
            logger.error(f"Error listening for Pipecat responses: {e}")

    async def handle_twilio_websocket(self, websocket):
        """Handle Twilio Media Stream WebSocket connection."""
        self.twilio_ws = websocket
        logger.info("Twilio WebSocket connected")

        try:
            # Connect to Pipecat
            if not await self.connect_to_pipecat():
                logger.error("Failed to connect to Pipecat, closing Twilio connection")
                return

            # Handle incoming messages from Twilio
            async for message in websocket:
                await self.audio_bridge.handle_twilio_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.info("Twilio WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in Twilio WebSocket handler: {e}")
        finally:
            if self.pipecat_ws:
                await self.pipecat_ws.close()
            logger.info("Cleaned up WebSocket connections")

    async def send_to_pipecat(self, pcm_audio: bytes):
        """Send audio data to Pipecat pipeline."""
        if self.pipecat_ws:
            try:
                # Create protobuf message for Pipecat (ProtobufFrameSerializer format)
                import base64

                # Pipecat expects base64-encoded audio in specific format
                audio_data = {
                    "type": "audio",
                    "data": base64.b64encode(pcm_audio).decode('utf-8'),
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "pcm"
                }

                await self.pipecat_ws.send(json.dumps(audio_data))
                logger.debug(f"Sent {len(pcm_audio)} bytes to Pipecat")

            except Exception as e:
                logger.error(f"Error sending audio to Pipecat: {e}")

    async def send_to_twilio(self, pcm_audio: bytes):
        """Send audio data to Twilio Media Stream."""
        if self.twilio_ws and self.stream_sid:
            try:
                base64_payload = self.audio_bridge.process_pipecat_audio(pcm_audio)

                if base64_payload:
                    media_message = {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {
                            "payload": base64_payload
                        }
                    }

                    await self.twilio_ws.send_text(json.dumps(media_message))
                    logger.debug(f"Sent {len(pcm_audio)} bytes to Twilio")

            except Exception as e:
                logger.error(f"Error sending audio to Twilio: {e}")

# Test functions for development
async def test_audio_conversion():
    """Test audio format conversion functions."""
    bridge = TwilioAudioBridge()

    # Create test mulaw data (silence)
    test_mulaw = b'\x00' * 160  # 20ms of silence at 8kHz
    test_base64 = base64.b64encode(test_mulaw).decode('utf-8')

    # Test Twilio -> Pipecat conversion
    pcm_result = bridge.process_twilio_audio(test_base64)
    logger.info(f"Twilio->Pipecat: {len(test_mulaw)} mulaw -> {len(pcm_result)} PCM")

    # Test Pipecat -> Twilio conversion
    base64_result = bridge.process_pipecat_audio(pcm_result)
    logger.info(f"Pipecat->Twilio: {len(pcm_result)} PCM -> {len(base64_result)} base64")

    logger.info("Audio conversion test completed")

if __name__ == "__main__":
    # Run audio conversion test
    asyncio.run(test_audio_conversion())