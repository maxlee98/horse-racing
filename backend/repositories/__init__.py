"""Repository layer for data access abstraction."""

from .base import RoomRepository
from .memory import InMemoryRoomRepository

__all__ = ["RoomRepository", "InMemoryRoomRepository"]
