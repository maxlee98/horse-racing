"""Abstract base class for room repositories."""

from abc import ABC, abstractmethod
from typing import Optional
from core.models import GameRoom


class RoomRepository(ABC):
    """Abstract repository for game rooms.
    
    This abstraction allows easy switching between in-memory storage
    (for development/testing) and persistent storage (Redis/PostgreSQL).
    """

    @abstractmethod
    def save(self, room: GameRoom) -> None:
        """Save or update a room."""
        pass

    @abstractmethod
    def get(self, room_id: str) -> Optional[GameRoom]:
        """Get a room by ID."""
        pass

    @abstractmethod
    def delete(self, room_id: str) -> bool:
        """Delete a room. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    def list_all(self) -> list[GameRoom]:
        """List all rooms."""
        pass

    @abstractmethod
    def exists(self, room_id: str) -> bool:
        """Check if a room exists."""
        pass
