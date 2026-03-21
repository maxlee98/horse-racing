"""WebSocket connection manager."""

from typing import Optional
from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections for game rooms.
    
    Handles:
    - Connection registration/unregistration
    - Broadcasting messages to all connections in a room
    - Handling disconnections gracefully
    """

    def __init__(self):
        # room_id -> { client_id -> WebSocket }
        self._connections: dict[str, dict[str, WebSocket]] = {}

    def connect(self, room_id: str, client_id: str, websocket: WebSocket) -> None:
        """Register a new WebSocket connection."""
        room_id = room_id.upper()
        if room_id not in self._connections:
            self._connections[room_id] = {}
        self._connections[room_id][client_id] = websocket

    def disconnect(self, room_id: str, client_id: str) -> None:
        """Unregister a WebSocket connection."""
        room_id = room_id.upper()
        if room_id in self._connections:
            self._connections[room_id].pop(client_id, None)
            # Clean up empty rooms
            if not self._connections[room_id]:
                del self._connections[room_id]

    async def broadcast(
        self,
        room_id: str,
        message: dict,
        exclude: Optional[str] = None
    ) -> None:
        """Broadcast a message to all connections in a room.
        
        Args:
            room_id: The room to broadcast to
            message: The message to send (will be JSON serialized)
            exclude: Optional client_id to exclude from broadcast
        """
        room_id = room_id.upper()
        if room_id not in self._connections:
            return

        dead_connections = []
        
        for client_id, websocket in self._connections[room_id].items():
            if client_id == exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                # Mark dead connections for cleanup
                dead_connections.append(client_id)

        # Clean up dead connections
        for client_id in dead_connections:
            self._connections[room_id].pop(client_id, None)

    async def send_to_client(
        self,
        room_id: str,
        client_id: str,
        message: dict
    ) -> bool:
        """Send a message to a specific client.
        
        Returns:
            True if sent successfully, False otherwise
        """
        room_id = room_id.upper()
        if room_id not in self._connections:
            return False
        
        websocket = self._connections[room_id].get(client_id)
        if not websocket:
            return False
        
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self._connections[room_id].pop(client_id, None)
            return False

    def get_connection_count(self, room_id: str) -> int:
        """Get the number of active connections in a room."""
        room_id = room_id.upper()
        return len(self._connections.get(room_id, {}))

    def is_connected(self, room_id: str, client_id: str) -> bool:
        """Check if a client is connected to a room."""
        room_id = room_id.upper()
        return client_id in self._connections.get(room_id, {})

    def get_room_ids(self) -> list[str]:
        """Get all room IDs with active connections."""
        return list(self._connections.keys())
