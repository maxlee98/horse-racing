"""Abstract base class for game mode strategies."""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Any
from core.models import GameRoom, Bet


class GameModeStrategy(ABC):
    """Abstract strategy for game modes.
    
    Each game mode implements:
    - Winner determination logic
    - Animation runner (if applicable)
    - Win condition checking
    - Probability calculation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the game mode name."""
        pass

    @abstractmethod
    def calculate_probabilities(self, room: GameRoom) -> None:
        """Calculate win probabilities for all bet options."""
        pass

    @abstractmethod
    async def run_animation(
        self,
        room: GameRoom,
        broadcast: Callable[[dict], Any]
    ) -> tuple[bool, str, Optional[str]]:
        """Run the game animation and determine winner.
        
        Returns: (success, message, winner_option_id)
        """
        pass

    @abstractmethod
    def check_win(self, bet: Bet, winning_value: Any) -> bool:
        """Check if a bet wins based on the winning value."""
        pass

    @abstractmethod
    def get_payout_multiplier(self, bet: Bet) -> int:
        """Get the payout multiplier for a bet."""
        pass

    def initialize_default_options(self, room: GameRoom) -> None:
        """Initialize default bet options for this game mode.
        
        Override in subclasses to provide game-specific default options.
        Called when switching game modes.
        """
        pass

    def on_round_start(self, room: GameRoom) -> None:
        """Hook called when a new round starts. Override if needed."""
        pass

    def on_game_end(self, room: GameRoom) -> None:
        """Hook called when the game ends. Override if needed."""
        pass

    def select_winner_by_probability(self, room: GameRoom) -> Optional[str]:
        """Select winner based on configured probabilities.
        
        Override for game-specific selection logic.
        Default: weighted random selection based on probabilities.
        
        Returns:
            The ID of the winning option, or None if no options exist.
        """
        if not room.bet_options:
            return None
        
        import random
        probs = [opt.probability for opt in room.bet_options]
        total_prob = sum(probs)
        
        if total_prob == 0:
            winner = random.choice(room.bet_options)
            return winner.id
        
        normalized = [p / total_prob for p in probs]
        r = random.random()
        cumulative = 0
        
        for i, prob in enumerate(normalized):
            cumulative += prob
            if r <= cumulative:
                return room.bet_options[i].id
        
        return room.bet_options[-1].id
