# app/services/connection_manager.py

from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # Tracks general connections: channel_name → list of websockets
        # e.g. "news" → [ws1, ws2, ws3]
        self.channels: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        """Accept a new WebSocket connection and add it to a channel."""
        await websocket.accept()
        if channel not in self.channels:
            self.channels[channel] = []
        self.channels[channel].append(websocket)
        print(f"[WS] Client connected to channel: {channel} | Total: {len(self.channels[channel])}")

    def disconnect(self, websocket: WebSocket, channel: str):
        """Remove a WebSocket from a channel when client disconnects."""
        if channel in self.channels:
            self.channels[channel].remove(websocket)
            print(f"[WS] Client disconnected from channel: {channel}")

    async def broadcast(self, channel: str, message: dict):
        """Send a message to every client connected to a channel."""
        if channel not in self.channels:
            return

        # Convert dict to JSON string once, send to all clients
        message_text = json.dumps(message)
        dead_connections = []

        for websocket in self.channels[channel]:
            try:
                await websocket.send_text(message_text)
            except Exception:
                # Client disconnected ungracefully — mark for cleanup
                dead_connections.append(websocket)

        # Clean up any dead connections
        for ws in dead_connections:
            self.channels[channel].remove(ws)


# Single shared instance — imported by routers that need to broadcast
manager = ConnectionManager()