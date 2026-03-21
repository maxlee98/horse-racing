"""Tests for InMemoryRoomRepository."""

import pytest
from core.models import GameRoom, GameStatus, GameMode
from repositories import InMemoryRoomRepository


class TestSaveAndGet:
    """Tests for basic save/get operations."""

    def test_save_and_get_roundtrip(self):
        """Room can be saved and retrieved."""
        repo = InMemoryRoomRepository()
        room = GameRoom(
            room_id="ABC123",
            host_id="host-1",
            title="Test Room",
            description="Test",
            status=GameStatus.WAITING,
            game_mode=GameMode.STANDARD,
        )
        
        repo.save(room)
        retrieved = repo.get("ABC123")
        
        assert retrieved is not None
        assert retrieved.room_id == "ABC123"
        assert retrieved.title == "Test Room"

    def test_get_nonexistent_returns_none(self):
        """Getting non-existent room returns None."""
        repo = InMemoryRoomRepository()
        result = repo.get("NONEXISTENT")
        assert result is None

    def test_get_case_insensitive(self):
        """Room IDs are case-insensitive."""
        repo = InMemoryRoomRepository()
        room = GameRoom(
            room_id="ABC123",
            host_id="host-1",
            title="Test Room",
            description="Test",
            status=GameStatus.WAITING,
            game_mode=GameMode.STANDARD,
        )
        
        repo.save(room)
        
        # Should find with lowercase
        assert repo.get("abc123") is not None
        # Should find with mixed case
        assert repo.get("AbC123") is not None

    def test_save_updates_existing(self):
        """Saving existing room updates it."""
        repo = InMemoryRoomRepository()
        room = GameRoom(
            room_id="ABC123",
            host_id="host-1",
            title="Original Title",
            description="Test",
            status=GameStatus.WAITING,
            game_mode=GameMode.STANDARD,
        )
        
        repo.save(room)
        
        # Modify and save again
        room.title = "Updated Title"
        repo.save(room)
        
        retrieved = repo.get("ABC123")
        assert retrieved.title == "Updated Title"


class TestDelete:
    """Tests for delete operations."""

    def test_delete_existing(self):
        """Delete returns True for existing room."""
        repo = InMemoryRoomRepository()
        room = GameRoom(
            room_id="ABC123",
            host_id="host-1",
            title="Test",
            description="Test",
            status=GameStatus.WAITING,
            game_mode=GameMode.STANDARD,
        )
        
        repo.save(room)
        result = repo.delete("ABC123")
        
        assert result is True
        assert repo.get("ABC123") is None

    def test_delete_nonexistent(self):
        """Delete returns False for non-existent room."""
        repo = InMemoryRoomRepository()
        result = repo.delete("NONEXISTENT")
        assert result is False


class TestListAll:
    """Tests for listing all rooms."""

    def test_list_all_empty(self):
        """Empty repo returns empty list."""
        repo = InMemoryRoomRepository()
        assert repo.list_all() == []

    def test_list_all_multiple(self):
        """Returns all saved rooms."""
        repo = InMemoryRoomRepository()
        
        for i in range(3):
            room = GameRoom(
                room_id=f"ROOM{i}",
                host_id=f"host-{i}",
                title=f"Room {i}",
                description="Test",
                status=GameStatus.WAITING,
                game_mode=GameMode.STANDARD,
            )
            repo.save(room)
        
        rooms = repo.list_all()
        assert len(rooms) == 3
        room_ids = {r.room_id for r in rooms}
        assert room_ids == {"ROOM0", "ROOM1", "ROOM2"}
