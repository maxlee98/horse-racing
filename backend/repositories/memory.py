"""In-memory implementation of room repository."""

from typing import Optional
from core.models import GameRoom
from .base import RoomRepository


class InMemoryRoomRepository(RoomRepository):
    """In-memory storage for game rooms.
    
    Note: Data is lost when the server restarts.
    For production, replace with Redis or PostgreSQL implementation.
    """

    def __init__(self):
        self._rooms: dict[str, GameRoom] = {}

    def save(self, room: GameRoom) -> None:
        """Save or update a room."""
        self._rooms[room.room_id.upper()] = room

    def get(self, room_id: str) -> Optional[GameRoom]:
        """Get a room by ID (case-insensitive)."""
        return self._rooms.get(room_id.upper())

    def delete(self, room_id: str) -> bool:
        """Delete a room."""
        room_id = room_id.upper()
        if room_id in self._rooms:
            del self._rooms[room_id]
            return True
        return False

    def list_all(self) -> list[GameRoom]:
        """List all rooms."""
        return list(self._rooms.values())

    def exists(self, room_id: str) -> bool:
        """Check if a room exists."""
        return room_id.upper() in self._rooms
