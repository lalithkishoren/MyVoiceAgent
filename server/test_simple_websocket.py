#!/usr/bin/env python3

import asyncio
import websockets
import json

async def test_websocket():
    """Test the WebSocket signaling endpoint."""
    try:
        async with websockets.connect("ws://localhost:8080/ws") as websocket:
            print("Connected to WebSocket signaling endpoint")

            # Send test message
            test_message = {
                "type": "test",
                "message": "Hello from test client"
            }
            await websocket.send(json.dumps(test_message))
            print(f"Sent: {test_message}")

            # Receive response
            response = await websocket.recv()
            print(f"Received: {response}")

            return True

    except Exception as e:
        print(f"WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    if success:
        print("WebSocket signaling endpoint is working!")
    else:
        print("WebSocket signaling endpoint test failed!")