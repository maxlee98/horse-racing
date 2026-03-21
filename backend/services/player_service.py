"""Player management service."""

from core.models import GameRoom, Player, GameStatus
from core.exceptions import RoomFullException, RoomNotFoundException


class PlayerService:
    """Service for managing players in game rooms."""

    def __init__(self, room_service):
        """Initialize with room service."""
        self._room_service = room_service

    def add_player(self, room_id: str, player_id: str, name: str) -> Player:
        """Add a player to a room.
        
        Args:
            room_id: The room ID
            player_id: The player's unique ID
            name: The player's display name
            
        Returns:
            The created Player object
            
        Raises:
            RoomNotFoundException: If room not found
            RoomFullException: If room is full
        """
        room = self._room_service.get_room(room_id)
        if not room:
            raise RoomNotFoundException(f"Room {room_id} not found")
        
        # Check if player already exists (reconnecting)
        if player_id in room.players:
            player = room.players[player_id]
            player.is_connected = True
            self._room_service._repo.save(room)
            return player
        
        # Check room capacity
        connected_count = len([p for p in room.players.values() if p.is_connected])
        if connected_count >= room.max_players:
            raise RoomFullException(f"Room {room_id} is full")
        
        # Create new player
        player = Player(id=player_id, name=name)
        room.players[player_id] = player
        self._room_service._repo.save(room)
        
        return player

    def remove_player(self, room_id: str, player_id: str) -> bool:
        """Mark a player as disconnected.
        
        Args:
            room_id: The room ID
            player_id: The player's ID
            
        Returns:
            True if player was removed, False if not found
        """
        room = self._room_service.get_room(room_id)
        if not room:
            return False
        
        if player_id in room.players:
            room.players[player_id].is_connected = False
            self._room_service._repo.save(room)
            return True
        
        return False

    def get_player(self, room: GameRoom, player_id: str) -> Player | None:
        """Get a player from a room."""
        return room.players.get(player_id)

    def get_connected_players(self, room: GameRoom) -> list[Player]:
        """Get all connected players in a room."""
        return [p for p in room.players.values() if p.is_connected]

    def update_balance(
        self,
        room_id: str,
        player_id: str,
        amount: float
    ) -> Player:
        """Update a player's balance.
        
        Args:
            room_id: The room ID
            player_id: The player's ID
            amount: Amount to add (can be negative)
            
        Returns:
            The updated Player
        """
        room = self._room_service.get_room_or_raise(room_id)
        player = room.players.get(player_id)
        
        if not player:
            raise ValueError(f"Player {player_id} not found")
        
        player.balance += amount
        self._room_service._repo.save(room)
        return player

    def reset_all_balances(self, room_id: str, default_balance: float = 1000.0) -> None:
        """Reset all player balances in a room.
        
        Args:
            room_id: The room ID
            default_balance: The default balance to set
        """
        room = self._room_service.get_room_or_raise(room_id)
        
        for player in room.players.values():
            player.balance = default_balance
        
        self._room_service._repo.save(room)

    def is_player_connected(self, room: GameRoom, player_id: str) -> bool:
        """Check if a player is connected."""
        player = room.players.get(player_id)
        return player.is_connected if player else False
