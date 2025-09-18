import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import weakref
import gc

from voice_session import VoiceSession
import structlog

logger = structlog.get_logger(__name__)


class SessionManager:
    """Global session management for voice agent sessions."""

    def __init__(
        self,
        max_sessions: int = 50,
        cleanup_interval: int = 300,  # 5 minutes
        session_timeout: int = 1800,  # 30 minutes
        gemini_api_key: str = None
    ):
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self.session_timeout = session_timeout

        # API key for voice sessions
        self.gemini_api_key = gemini_api_key

        # Session storage
        self.sessions: Dict[str, VoiceSession] = {}
        self.sessions_by_websocket: Dict[Any, str] = {}

        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Metrics
        self.metrics = {
            "total_sessions_created": 0,
            "total_sessions_ended": 0,
            "current_active_sessions": 0,
            "max_concurrent_sessions": 0,
            "sessions_expired": 0,
            "sessions_failed": 0,
            "cleanup_runs": 0
        }

        logger.info("Session manager initialized",
                   max_sessions=max_sessions,
                   cleanup_interval=cleanup_interval,
                   session_timeout=session_timeout)

    async def start(self) -> None:
        """Start the session manager and cleanup task."""
        if self.is_running:
            return

        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("Session manager started")

    async def stop(self) -> None:
        """Stop the session manager and cleanup all sessions."""
        if not self.is_running:
            return

        self.is_running = False

        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # End all active sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.end_session(session_id)

        logger.info("Session manager stopped",
                   total_sessions_ended=len(session_ids))

    async def create_session(
        self,
        websocket_handler,
        session_id: str = None,
        system_prompt: str = None
    ) -> Optional[VoiceSession]:
        """Create a new voice session."""
        try:
            # Check session limit
            if len(self.sessions) >= self.max_sessions:
                logger.warning("Maximum sessions reached",
                             current_sessions=len(self.sessions),
                             max_sessions=self.max_sessions)
                return None

            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())

            # Check if session already exists
            if session_id in self.sessions:
                logger.warning("Session ID already exists", session_id=session_id)
                return None

            # Validate API key
            if not self.gemini_api_key:
                logger.error("Missing required Gemini API key for session creation")
                return None

            # Create new session
            session = VoiceSession(
                session_id=session_id,
                websocket_handler=websocket_handler,
                gemini_api_key=self.gemini_api_key,
                system_prompt=system_prompt,
                session_timeout=self.session_timeout
            )

            # Initialize session
            if not await session.initialize():
                logger.error("Failed to initialize session", session_id=session_id)
                self.metrics["sessions_failed"] += 1
                return None

            # Store session
            self.sessions[session_id] = session
            self.sessions_by_websocket[websocket_handler] = session_id

            # Update metrics
            self.metrics["total_sessions_created"] += 1
            self.metrics["current_active_sessions"] = len(self.sessions)
            self.metrics["max_concurrent_sessions"] = max(
                self.metrics["max_concurrent_sessions"],
                len(self.sessions)
            )

            logger.info("Session created successfully",
                       session_id=session_id,
                       total_sessions=len(self.sessions))

            return session

        except Exception as e:
            logger.error("Error creating session",
                        session_id=session_id,
                        error=str(e))
            self.metrics["sessions_failed"] += 1
            return None

    async def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    async def get_session_by_websocket(self, websocket_handler) -> Optional[VoiceSession]:
        """Get session by websocket handler."""
        session_id = self.sessions_by_websocket.get(websocket_handler)
        if session_id:
            return self.sessions.get(session_id)
        return None

    async def end_session(self, session_id: str) -> bool:
        """End a session and cleanup resources."""
        try:
            session = self.sessions.get(session_id)
            if not session:
                logger.warning("Session not found for ending", session_id=session_id)
                return False

            # Remove from websocket mapping
            websocket_to_remove = None
            for ws, sid in self.sessions_by_websocket.items():
                if sid == session_id:
                    websocket_to_remove = ws
                    break

            if websocket_to_remove:
                del self.sessions_by_websocket[websocket_to_remove]

            # End the session
            await session.end_session()

            # Remove from sessions
            del self.sessions[session_id]

            # Update metrics
            self.metrics["total_sessions_ended"] += 1
            self.metrics["current_active_sessions"] = len(self.sessions)

            logger.info("Session ended successfully",
                       session_id=session_id,
                       remaining_sessions=len(self.sessions))

            return True

        except Exception as e:
            logger.error("Error ending session",
                        session_id=session_id,
                        error=str(e))
            return False

    async def end_session_by_websocket(self, websocket_handler) -> bool:
        """End session by websocket handler."""
        session_id = self.sessions_by_websocket.get(websocket_handler)
        if session_id:
            return await self.end_session(session_id)
        return False

    async def handle_websocket_disconnect(self, websocket_handler) -> None:
        """Handle websocket disconnection."""
        try:
            session_id = self.sessions_by_websocket.get(websocket_handler)
            if session_id:
                logger.info("Handling websocket disconnect",
                           session_id=session_id)
                await self.end_session(session_id)

        except Exception as e:
            logger.error("Error handling websocket disconnect",
                        error=str(e))

    async def _cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions."""
        try:
            expired_sessions = []

            for session_id, session in self.sessions.items():
                if session.is_expired():
                    expired_sessions.append(session_id)

            # End expired sessions
            for session_id in expired_sessions:
                logger.info("Cleaning up expired session", session_id=session_id)
                await self.end_session(session_id)
                self.metrics["sessions_expired"] += 1

            if expired_sessions:
                logger.info("Expired sessions cleaned up",
                           count=len(expired_sessions))

            return len(expired_sessions)

        except Exception as e:
            logger.error("Error during session cleanup", error=str(e))
            return 0

    async def _cleanup_loop(self) -> None:
        """Background task for session cleanup."""
        logger.info("Session cleanup loop started",
                   interval=self.cleanup_interval)

        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)

                if not self.is_running:
                    break

                # Run cleanup
                cleaned_count = await self._cleanup_expired_sessions()
                self.metrics["cleanup_runs"] += 1

                # Force garbage collection periodically
                if self.metrics["cleanup_runs"] % 12 == 0:  # Every hour with 5-min intervals
                    gc.collect()
                    logger.debug("Forced garbage collection")

                logger.debug("Session cleanup completed",
                           cleaned_sessions=cleaned_count,
                           active_sessions=len(self.sessions))

            except asyncio.CancelledError:
                logger.info("Session cleanup loop cancelled")
                break
            except Exception as e:
                logger.error("Error in session cleanup loop", error=str(e))
                await asyncio.sleep(60)  # Wait before retrying

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get information about all active sessions."""
        return [
            session.get_session_info()
            for session in self.sessions.values()
        ]

    def get_session_count(self) -> int:
        """Get current session count."""
        return len(self.sessions)

    def get_metrics(self) -> Dict[str, Any]:
        """Get session manager metrics."""
        return {
            **self.metrics.copy(),
            "current_session_count": len(self.sessions),
            "sessions_by_websocket_count": len(self.sessions_by_websocket)
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of session manager."""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "active_sessions": len(self.sessions),
            "max_sessions": self.max_sessions,
            "utilization_percent": (len(self.sessions) / self.max_sessions) * 100,
            "cleanup_task_running": self.cleanup_task and not self.cleanup_task.done(),
            "metrics": self.get_metrics()
        }

    async def force_cleanup(self) -> Dict[str, int]:
        """Force immediate cleanup of expired sessions."""
        logger.info("Force cleanup requested")
        cleaned_count = await self._cleanup_expired_sessions()
        return {
            "cleaned_sessions": cleaned_count,
            "remaining_sessions": len(self.sessions)
        }