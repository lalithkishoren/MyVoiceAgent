#!/usr/bin/env python3

import pkgutil
import pipecat.transports

print("Available Pipecat transport modules:")
for importer, modname, ispkg in pkgutil.walk_packages(pipecat.transports.__path__, pipecat.transports.__name__ + '.'):
    print(f"  {modname} {'(package)' if ispkg else ''}")

print("\nChecking for WebRTC-related transports:")
try:
    import pipecat.transports.daily
    print("✅ Daily.co transport available")
except ImportError:
    print("❌ Daily.co transport not available")

try:
    import pipecat.transports.websocket
    print("✅ WebSocket transport available")
except ImportError:
    print("❌ WebSocket transport not available")

try:
    import pipecat.transports.webrtc
    print("✅ WebRTC transport available")
except ImportError:
    print("❌ WebRTC transport not available")

try:
    import pipecat.transports.network
    print("✅ Network transport available")
except ImportError:
    print("❌ Network transport not available")

print("\nChecking installed Pipecat extras:")
try:
    import pipecat
    print(f"Pipecat version: {pipecat.__version__}")
except:
    print("Could not determine Pipecat version")