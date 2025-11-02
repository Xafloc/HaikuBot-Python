"""WebSocket support for real-time haiku feed."""

import logging
import asyncio
import json
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

websocket_router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients.
        
        Args:
            message: Message dictionary to broadcast
        """
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        
        # Send to all connections, removing any that fail
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove failed connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client.
        
        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            self.disconnect(websocket)


# Global connection manager instance
manager = ConnectionManager()


@websocket_router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live haiku feed.
    
    Clients connect here to receive real-time notifications when
    new haikus are generated.
    
    Args:
        websocket: WebSocket connection
    """
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal({
            "type": "connected",
            "message": "Connected to HaikuBot live feed"
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Handle ping
                if data == "ping":
                    await manager.send_personal({"type": "pong"}, websocket)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    finally:
        manager.disconnect(websocket)


async def broadcast_new_haiku(haiku_data: dict):
    """Broadcast a new haiku to all connected clients.
    
    This function is called from IRC bot when a new haiku is generated.
    
    Args:
        haiku_data: Dictionary with haiku information
    """
    message = {
        "type": "new_haiku",
        "data": haiku_data
    }
    
    await manager.broadcast(message)


async def broadcast_new_line(line_data: dict):
    """Broadcast a new line collection to all connected clients.
    
    Args:
        line_data: Dictionary with line information
    """
    message = {
        "type": "new_line",
        "data": line_data
    }
    
    await manager.broadcast(message)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager.
    
    Returns:
        ConnectionManager instance
    """
    return manager

