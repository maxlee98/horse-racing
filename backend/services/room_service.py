"""Room management service."""

import uuid
from typing import Optional
from core.models import GameRoom, GameStatus, BetOption, GameMode
from core.exceptions import RoomNotFoundException, NotAuthorizedException
from repositories.base import RoomRepository
from game_modes import get_game_mode


class RoomService:
    """Service for room CRUD operations and lifecycle management."""

    def __init__(self, repository: RoomRepository):
        self._repo = repository

    def _recalculate_odds_from_probabilities(self, room: GameRoom) -> None:
        """Recalculate odds based on updated probabilities.

        Args:
            room: The game room with updated probabilities.
        """
        for option in room.bet_options:
            if option.probability and option.probability > 0:
                option.odds = round(1.0 / option.probability, 2)

    def create_room(
        self,
        host_id: str,
        title: str,
        description: str,
        bet_options: list[dict],
        game_mode: GameMode = GameMode.STANDARD,
        use_randomized_probabilities: bool = False
    ) -> GameRoom:
        """Create a new game room."""
        room_id = str(uuid.uuid4())[:8].upper()
        
        # Convert dict options to BetOption models
        options = [BetOption(**opt) for opt in bet_options] if bet_options else []
        
        # Create room
        room = GameRoom(
            room_id=room_id,
            host_id=host_id,
            title=title,
            description=description,
            bet_options=options,
            game_mode=game_mode,
            use_randomized_probabilities=use_randomized_probabilities,
        )
        
        # Calculate initial probabilities using game mode strategy
        game_mode_strategy = get_game_mode(game_mode.value)
        game_mode_strategy.calculate_probabilities(room)
        
        # Save room
        self._repo.save(room)
        return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """Get a room by ID."""
        return self._repo.get(room_id)

    def get_room_or_raise(self, room_id: str) -> GameRoom:
        """Get a room or raise RoomNotFoundException."""
        room = self._repo.get(room_id)
        if not room:
            raise RoomNotFoundException(f"Room {room_id} not found")
        return room

    def update_status(
        self,
        room_id: str,
        status: GameStatus,
        host_id: str
    ) -> GameRoom:
        """Update room status."""
        room = self.get_room_or_raise(room_id)
        
        if room.host_id != host_id:
            raise NotAuthorizedException("Only host can update status")
        
        room.status = status
        self._repo.save(room)
        return room

    def set_winner(
        self,
        room_id: str,
        option_id: str,
        host_id: str
    ) -> GameRoom:
        """Set the winning option."""
        room = self.get_room_or_raise(room_id)
        
        if room.host_id != host_id:
            raise NotAuthorizedException("Only host can set winner")
        
        # Validate option exists
        option = next((o for o in room.bet_options if o.id == option_id), None)
        if not option:
            raise ValueError(f"Invalid option: {option_id}")
        
        room.winner_option_id = option_id
        room.status = GameStatus.ENDED
        self._repo.save(room)
        return room

    def update_bet_options(
        self,
        room_id: str,
        bet_options: list[dict],
        host_id: str
    ) -> GameRoom:
        """Update bet options."""
        room = self.get_room_or_raise(room_id)
        
        if room.host_id != host_id:
            raise NotAuthorizedException("Only host can update options")
        
        room.bet_options = [BetOption(**opt) for opt in bet_options]
        
        # Recalculate probabilities
        game_mode_strategy = get_game_mode(room.game_mode.value)
        game_mode_strategy.calculate_probabilities(room)
        
        self._repo.save(room)
        return room

    def update_probabilities(
        self,
        room_id: str,
        probabilities: dict[str, float],
        host_id: str
    ) -> GameRoom:
        """Update win probabilities."""
        room = self.get_room_or_raise(room_id)
        
        if room.host_id != host_id:
            raise NotAuthorizedException("Only host can update probabilities")
        
        for option in room.bet_options:
            if option.id in probabilities:
                option.probability = max(0.01, min(1.0, probabilities[option.id]))
        
        # Recalculate odds based on new probabilities
        self._recalculate_odds_from_probabilities(room)
        
        self._repo.save(room)
        return room

    def randomize_probabilities(self, room_id: str, host_id: str) -> GameRoom:
        """Randomize probabilities for a new round."""
        room = self.get_room_or_raise(room_id)
        
        if room.host_id != host_id:
            raise NotAuthorizedException("Only host can randomize")
        
        if not room.bet_options:
            raise ValueError("No bet options")
        
        # Generate random probabilities
        import random
        raw_probs = [random.random() for _ in room.bet_options]
        total = sum(raw_probs)
        normalized = [p / total for p in raw_probs]
        
        for i, option in enumerate(room.bet_options):
            option.probability = round(normalized[i], 4)
        
        # Recalculate odds based on new probabilities
        self._recalculate_odds_from_probabilities(room)
        
        self._repo.save(room)
        return room

    def next_round(self, room_id: str, host_id: str) -> GameRoom:
        """Start a new round."""
        room = self.get_room_or_raise(room_id)
        
        if room.host_id != host_id:
            raise NotAuthorizedException("Only host can start next round")
        
        # Clear bets and winner
        room.bets = []
        room.winner_option_id = None
        room.status = GameStatus.WAITING
        room.round_number += 1
        
        # Randomize probabilities
        self.randomize_probabilities(room_id, host_id)
        
        return room

    def reset_lobby(self, room_id: str, host_id: str) -> GameRoom:
        """Reset the entire lobby."""
        room = self.get_room_or_raise(room_id)
        
        if room.host_id != host_id:
            raise NotAuthorizedException("Only host can reset")
        
        room.status = GameStatus.WAITING
        room.bets = []
        room.winner_option_id = None
        room.round_number = 1
        
        # Reset player balances
        for player in room.players.values():
            player.balance = 1000.0
        
        # Reset probabilities
        if room.bet_options:
            prob = 1.0 / len(room.bet_options)
            for opt in room.bet_options:
                opt.probability = prob
        
        self._repo.save(room)
        return room

    def delete_room(self, room_id: str, host_id: str) -> bool:
        """Delete a room."""
        room = self.get_room_or_raise(room_id)
        
        if room.host_id != host_id:
            raise NotAuthorizedException("Only host can delete room")
        
        return self._repo.delete(room_id)

    def to_dict(self, room: GameRoom) -> dict:
        """Convert room to dictionary for API response."""
        return {
            "room_id": room.room_id,
            "title": room.title,
            "description": room.description,
            "status": room.status,
            "bet_options": [o.model_dump() for o in room.bet_options],
            "players": {pid: p.model_dump() for pid, p in room.players.items()},
            "bets": [b.model_dump() for b in room.bets],
            "winner_option_id": room.winner_option_id,
            "max_players": room.max_players,
            "player_count": len([p for p in room.players.values() if p.is_connected]),
            "game_mode": room.game_mode.value,
            "round_number": room.round_number,
            "use_randomized_probabilities": room.use_randomized_probabilities,
            "roulette_history": room.roulette_history,
        }
