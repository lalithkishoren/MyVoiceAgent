import json
import asyncio
from typing import Dict, Any, Optional, Set
from datetime import datetime
import uuid

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

import structlog

logger = structlog.get_logger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections and message routing for voice sessions."""

    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.client_sessions: Dict[WebSocketServerProtocol, str] = {}

        logger.info("WebSocket handler initialized")

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle new WebSocket connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"

        try:
            logger.info("New WebSocket connection",
                       client_id=client_id,
                       path=path)

            # Add to connected clients
            self.connected_clients.add(websocket)

            # Send welcome message
            await self._send_message(websocket, {
                "type": "connection-established",
                "message": "Connected to Sutherland Voice Agent",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Handle messages from this client
            await self._handle_client_messages(websocket, client_id)

        except ConnectionClosed:
            logger.info("Client disconnected", client_id=client_id)
        except WebSocketException as e:
            logger.warning("WebSocket error", client_id=client_id, error=str(e))
        except Exception as e:
            logger.error("Unexpected error handling connection",
                        client_id=client_id, error=str(e))
        finally:
            await self._cleanup_client(websocket)

    async def _handle_client_messages(self, websocket: WebSocketServerProtocol, client_id: str) -> None:
        """Handle messages from a specific client."""
        async for message in websocket:
            try:
                # Parse JSON message
                if isinstance(message, bytes):
                    message = message.decode('utf-8')

                data = json.loads(message)

                logger.debug("Received message",
                           client_id=client_id,
                           message_type=data.get("type"))

                # Route message based on type
                await self._route_message(websocket, data, client_id)

            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON message",
                             client_id=client_id,
                             error=str(e))
                await self._send_error(websocket, "Invalid JSON format")

            except Exception as e:
                logger.error("Error processing message",
                           client_id=client_id,
                           error=str(e))
                await self._send_error(websocket, "Internal server error")

    async def _route_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any], client_id: str) -> None:
        """Route message to appropriate handler based on type."""
        message_type = data.get("type")

        if not message_type:
            await self._send_error(websocket, "Missing message type")
            return

        try:
            if message_type == "start-session":
                await self._handle_start_session(websocket, data, client_id)
            elif message_type == "end-session":
                await self._handle_end_session(websocket, data, client_id)
            elif message_type == "offer":
                await self._handle_webrtc_offer(websocket, data, client_id)
            elif message_type == "answer":
                await self._handle_webrtc_answer(websocket, data, client_id)
            elif message_type == "ice-candidate":
                await self._handle_ice_candidate(websocket, data, client_id)
            elif message_type == "ping":
                await self._handle_ping(websocket, data, client_id)
            else:
                logger.warning("Unknown message type",
                             message_type=message_type,
                             client_id=client_id)
                await self._send_error(websocket, f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error("Error routing message",
                        message_type=message_type,
                        client_id=client_id,
                        error=str(e))
            await self._send_error(websocket, "Failed to process message")

    async def _handle_start_session(self, websocket: WebSocketServerProtocol, data: Dict[str, Any], client_id: str) -> None:
        """Handle session start request."""
        try:
            # Check if client already has a session
            if websocket in self.client_sessions:
                existing_session_id = self.client_sessions[websocket]
                logger.warning("Client already has active session",
                             client_id=client_id,
                             existing_session_id=existing_session_id)
                await self._send_error(websocket, "Session already active")
                return

            # Extract session parameters
            session_id = data.get("sessionId") or str(uuid.uuid4())
            system_prompt = data.get("systemPrompt")
            offer = data.get("offer")

            # Create new session
            session = await self.session_manager.create_session(
                websocket_handler=websocket,
                session_id=session_id,
                system_prompt=system_prompt
            )

            if not session:
                logger.error("Failed to create session", client_id=client_id)
                await self._send_error(websocket, "Failed to create session")
                return

            # Store session mapping
            self.client_sessions[websocket] = session_id

            # Start the session
            if not await session.start():
                logger.error("Failed to start session",
                           session_id=session_id,
                           client_id=client_id)
                await self.session_manager.end_session(session_id)
                del self.client_sessions[websocket]
                await self._send_error(websocket, "Failed to start session")
                return

            logger.info("Session started successfully",
                       session_id=session_id,
                       client_id=client_id)

            # Send session created response
            await self._send_message(websocket, {
                "type": "session-created",
                "sessionId": session_id,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Handle WebRTC offer if provided
            if offer:
                answer = await session.handle_webrtc_offer(offer)
                if answer:
                    await self._send_message(websocket, {
                        "type": "answer",
                        "answer": answer,
                        "sessionId": session_id
                    })
                else:
                    logger.error("Failed to process WebRTC offer",
                               session_id=session_id)
                    await self._send_error(websocket, "Failed to process WebRTC offer")

        except Exception as e:
            logger.error("Error starting session",
                        client_id=client_id,
                        error=str(e))
            await self._send_error(websocket, "Failed to start session")

    async def _handle_end_session(self, websocket: WebSocketServerProtocol, data: Dict[str, Any], client_id: str) -> None:
        """Handle session end request."""
        try:
            session_id = self.client_sessions.get(websocket)

            if not session_id:
                logger.warning("No active session to end", client_id=client_id)
                await self._send_error(websocket, "No active session")
                return

            # End the session
            success = await self.session_manager.end_session(session_id)

            if success:
                del self.client_sessions[websocket]

                await self._send_message(websocket, {
                    "type": "session-ended",
                    "sessionId": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })

                logger.info("Session ended successfully",
                           session_id=session_id,
                           client_id=client_id)
            else:
                logger.error("Failed to end session",
                           session_id=session_id,
                           client_id=client_id)
                await self._send_error(websocket, "Failed to end session")

        except Exception as e:
            logger.error("Error ending session",
                        client_id=client_id,
                        error=str(e))
            await self._send_error(websocket, "Failed to end session")

    async def _handle_webrtc_offer(self, websocket: WebSocketServerProtocol, data: Dict[str, Any], client_id: str) -> None:
        """Handle WebRTC offer."""
        try:
            session_id = self.client_sessions.get(websocket)

            if not session_id:
                await self._send_error(websocket, "No active session")
                return

            session = await self.session_manager.get_session(session_id)
            if not session:
                await self._send_error(websocket, "Session not found")
                return

            offer = data.get("offer")
            if not offer:
                await self._send_error(websocket, "Missing offer")
                return

            # Process offer and get answer
            answer = await session.handle_webrtc_offer(offer)

            if answer:
                await self._send_message(websocket, {
                    "type": "answer",
                    "answer": answer,
                    "sessionId": session_id
                })
            else:
                await self._send_error(websocket, "Failed to process offer")

        except Exception as e:
            logger.error("Error handling WebRTC offer",
                        client_id=client_id,
                        error=str(e))
            await self._send_error(websocket, "Failed to process offer")

    async def _handle_webrtc_answer(self, websocket: WebSocketServerProtocol, data: Dict[str, Any], client_id: str) -> None:
        """Handle WebRTC answer."""
        try:
            session_id = self.client_sessions.get(websocket)

            if not session_id:
                await self._send_error(websocket, "No active session")
                return

            session = await self.session_manager.get_session(session_id)
            if not session:
                await self._send_error(websocket, "Session not found")
                return

            answer = data.get("answer")
            if not answer:
                await self._send_error(websocket, "Missing answer")
                return

            # Process answer
            success = await session.handle_webrtc_answer(answer)

            if not success:
                await self._send_error(websocket, "Failed to process answer")

        except Exception as e:
            logger.error("Error handling WebRTC answer",
                        client_id=client_id,
                        error=str(e))
            await self._send_error(websocket, "Failed to process answer")

    async def _handle_ice_candidate(self, websocket: WebSocketServerProtocol, data: Dict[str, Any], client_id: str) -> None:
        """Handle ICE candidate."""
        try:
            session_id = self.client_sessions.get(websocket)

            if not session_id:
                await self._send_error(websocket, "No active session")
                return

            session = await self.session_manager.get_session(session_id)
            if not session:
                await self._send_error(websocket, "Session not found")
                return

            candidate = data.get("candidate")
            if not candidate:
                await self._send_error(websocket, "Missing candidate")
                return

            # Process ICE candidate
            success = await session.handle_ice_candidate(candidate)

            if not success:
                logger.warning("Failed to process ICE candidate",
                             session_id=session_id,
                             client_id=client_id)

        except Exception as e:
            logger.error("Error handling ICE candidate",
                        client_id=client_id,
                        error=str(e))

    async def _handle_ping(self, websocket: WebSocketServerProtocol, data: Dict[str, Any], client_id: str) -> None:
        """Handle ping message."""
        try:
            await self._send_message(websocket, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Update session activity if exists
            session_id = self.client_sessions.get(websocket)
            if session_id:
                session = await self.session_manager.get_session(session_id)
                if session:
                    session.update_activity()

        except Exception as e:
            logger.error("Error handling ping",
                        client_id=client_id,
                        error=str(e))

    async def _send_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]) -> bool:
        """Send message to websocket client."""
        try:
            message = json.dumps(data)
            await websocket.send(message)
            return True
        except ConnectionClosed:
            logger.debug("Cannot send message, connection closed")
            return False
        except Exception as e:
            logger.error("Error sending message", error=str(e))
            return False

    async def _send_error(self, websocket: WebSocketServerProtocol, message: str) -> None:
        """Send error message to client."""
        await self._send_message(websocket, {
            "type": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _cleanup_client(self, websocket: WebSocketServerProtocol) -> None:
        """Cleanup client connection and associated session."""
        try:
            # Remove from connected clients
            self.connected_clients.discard(websocket)

            # End associated session
            session_id = self.client_sessions.get(websocket)
            if session_id:
                await self.session_manager.end_session(session_id)
                del self.client_sessions[websocket]

            logger.debug("Client cleanup completed",
                        session_id=session_id)

        except Exception as e:
            logger.error("Error during client cleanup", error=str(e))

    def get_connected_clients_count(self) -> int:
        """Get number of connected clients."""
        return len(self.connected_clients)

    def get_active_sessions_count(self) -> int:
        """Get number of active sessions."""
        return len(self.client_sessions)

    def get_handler_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "connected_clients": len(self.connected_clients),
            "active_sessions": len(self.client_sessions),
            "clients_with_sessions": len([
                ws for ws in self.connected_clients
                if ws in self.client_sessions
            ])
        }