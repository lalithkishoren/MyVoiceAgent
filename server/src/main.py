import os
import sys
import asyncio
import signal
from typing import Dict, Any
from datetime import datetime

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import websockets
from websockets.server import serve
from dotenv import load_dotenv

import structlog

# Import our modules
from session_manager import SessionManager
from websocket_handler import WebSocketHandler

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class PipecatVoiceServer:
    """Main Sutherland Voice Agent Server."""

    def __init__(self):
        # Load configuration
        self.port = int(os.getenv("PORT", 8080))
        self.host = os.getenv("HOST", "0.0.0.0")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_sessions = int(os.getenv("MAX_SESSIONS", 50))
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", 1800))  # 30 minutes

        # API key
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Validate required API key
        self._validate_api_key()

        # Initialize components
        self.session_manager = SessionManager(
            max_sessions=self.max_sessions,
            session_timeout=self.session_timeout,
            gemini_api_key=self.gemini_api_key
        )

        self.websocket_handler = WebSocketHandler(self.session_manager)

        # FastAPI app
        self.app = self._create_fastapi_app()

        # WebSocket server
        self.websocket_server = None

        # Server state
        self.is_running = False
        self.start_time = datetime.utcnow()

        logger.info("Pipecat Voice Server initialized",
                   port=self.port,
                   host=self.host,
                   max_sessions=self.max_sessions)

    def _validate_api_key(self) -> None:
        """Validate required API key."""
        if not self.gemini_api_key:
            logger.error("Missing required Gemini API key")
            raise ValueError("Missing required GEMINI_API_KEY environment variable")

    def _create_fastapi_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        app = FastAPI(
            title="Sutherland Voice Agent Server",
            description="Self-hosted WebRTC voice agent backend powered by Pipecat",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            try:
                uptime = datetime.utcnow() - self.start_time
                session_health = self.session_manager.get_health_status()
                handler_stats = self.websocket_handler.get_handler_stats()

                return JSONResponse({
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "uptime_seconds": uptime.total_seconds(),
                    "server": {
                        "is_running": self.is_running,
                        "port": self.port,
                        "host": self.host
                    },
                    "session_manager": session_health,
                    "websocket_handler": handler_stats
                })

            except Exception as e:
                logger.error("Health check failed", error=str(e))
                raise HTTPException(status_code=500, detail="Health check failed")

        # Sessions endpoint
        @app.get("/sessions")
        async def get_sessions():
            """Get information about active sessions."""
            try:
                sessions = self.session_manager.get_active_sessions()
                metrics = self.session_manager.get_metrics()

                return JSONResponse({
                    "sessions": sessions,
                    "metrics": metrics,
                    "timestamp": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.error("Failed to get sessions", error=str(e))
                raise HTTPException(status_code=500, detail="Failed to get sessions")

        # Force cleanup endpoint
        @app.post("/cleanup")
        async def force_cleanup():
            """Force cleanup of expired sessions."""
            try:
                result = await self.session_manager.force_cleanup()

                return JSONResponse({
                    "message": "Cleanup completed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.error("Force cleanup failed", error=str(e))
                raise HTTPException(status_code=500, detail="Cleanup failed")

        # Metrics endpoint
        @app.get("/metrics")
        async def get_metrics():
            """Get server metrics."""
            try:
                uptime = datetime.utcnow() - self.start_time
                session_metrics = self.session_manager.get_metrics()
                handler_stats = self.websocket_handler.get_handler_stats()

                return JSONResponse({
                    "timestamp": datetime.utcnow().isoformat(),
                    "uptime_seconds": uptime.total_seconds(),
                    "session_manager": session_metrics,
                    "websocket_handler": handler_stats,
                    "server": {
                        "is_running": self.is_running,
                        "start_time": self.start_time.isoformat()
                    }
                })

            except Exception as e:
                logger.error("Failed to get metrics", error=str(e))
                raise HTTPException(status_code=500, detail="Failed to get metrics")

        # Root endpoint
        @app.get("/")
        async def root():
            """Root endpoint."""
            return JSONResponse({
                "message": "Sutherland Voice Agent Server",
                "version": "1.0.0",
                "status": "running" if self.is_running else "stopped",
                "websocket_url": f"ws://{self.host}:{self.port}/ws",
                "docs_url": "/docs",
                "health_url": "/health"
            })

        return app

    async def start_websocket_server(self) -> None:
        """Start the WebSocket server."""
        try:
            logger.info("Starting WebSocket server",
                       host=self.host,
                       port=self.port)

            self.websocket_server = await serve(
                self.websocket_handler.handle_connection,
                self.host,
                self.port,
                path="/ws"
            )

            logger.info("WebSocket server started successfully")

        except Exception as e:
            logger.error("Failed to start WebSocket server", error=str(e))
            raise

    async def stop_websocket_server(self) -> None:
        """Stop the WebSocket server."""
        if self.websocket_server:
            try:
                logger.info("Stopping WebSocket server")
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
                logger.info("WebSocket server stopped")
            except Exception as e:
                logger.error("Error stopping WebSocket server", error=str(e))

    async def start(self) -> None:
        """Start the voice server."""
        try:
            logger.info("Starting Pipecat Voice Server")

            # Start session manager
            await self.session_manager.start()

            # Start WebSocket server
            await self.start_websocket_server()

            self.is_running = True
            self.start_time = datetime.utcnow()

            logger.info("Pipecat Voice Server started successfully",
                       host=self.host,
                       port=self.port)

        except Exception as e:
            logger.error("Failed to start server", error=str(e))
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the voice server."""
        try:
            logger.info("Stopping Pipecat Voice Server")

            self.is_running = False

            # Stop WebSocket server
            await self.stop_websocket_server()

            # Stop session manager
            await self.session_manager.stop()

            logger.info("Pipecat Voice Server stopped successfully")

        except Exception as e:
            logger.error("Error stopping server", error=str(e))

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def run_server():
    """Run the voice server."""
    server = PipecatVoiceServer()

    try:
        # Setup signal handlers
        server.setup_signal_handlers()

        # Start the server
        await server.start()

        # Run FastAPI server
        config = uvicorn.Config(
            app=server.app,
            host=server.host,
            port=server.port + 1,  # Use different port for HTTP API
            log_level=server.log_level.lower(),
            access_log=True
        )

        api_server = uvicorn.Server(config)

        # Run both servers concurrently
        logger.info("Starting HTTP API server", port=server.port + 1)

        await asyncio.gather(
            api_server.serve(),
            asyncio.Event().wait()  # Keep running until interrupted
        )

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Server error", error=str(e))
    finally:
        await server.stop()


def main():
    """Main entry point."""
    try:
        # Configure logging level
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        logger.info("Starting Sutherland Voice Agent Server",
                   log_level=log_level,
                   python_version=sys.version)

        # Run the server
        asyncio.run(run_server())

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()