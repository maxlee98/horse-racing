"""Standard betting game mode."""

import random
from typing import Optional, Callable, Any
from core.models import GameRoom, Bet, GameStatus, BetOption
from .base import GameModeStrategy


class StandardGameMode(GameModeStrategy):
    """Standard betting game where host manually declares winner."""

    @property
    def name(self) -> str:
        return "standard"

    def initialize_default_options(self, room: GameRoom) -> None:
        """Set up standard betting options (generic)."""
        room.bet_options = [
            BetOption(id="standard_opt_1", label="Option A", odds=2.0, probability=0.5),
            BetOption(id="standard_opt_2", label="Option B", odds=2.0, probability=0.5),
        ]

    def calculate_probabilities(self, room: GameRoom) -> None:
        """Calculate probabilities based on inverse odds."""
        if not room.bet_options:
            return
        
        # Inverse odds: 1/odds gives weight, normalize to get probability
        inverse_odds = [1.0 / opt.odds for opt in room.bet_options]
        total_inverse = sum(inverse_odds)
        
        for i, opt in enumerate(room.bet_options):
            opt.probability = round(inverse_odds[i] / total_inverse, 4)

    async def run_animation(
        self,
        room: GameRoom,
        broadcast: Callable[[dict], Any]
    ) -> tuple[bool, str, Optional[str]]:
        """Standard mode has no animation - host declares winner manually."""
        # Just lock the bets, host will declare winner
        room.status = GameStatus.LOCKED
        return True, "Bets locked. Waiting for host to declare winner.", None

    def check_win(self, bet: Bet, winning_value: Any) -> bool:
        """Check if bet wins - in standard mode, compare option_id."""
        return bet.option_id == winning_value

    def get_payout_multiplier(self, bet: Bet) -> int:
        """Standard mode uses the odds from bet options."""
        # Returns the odds as integer (simplified)
        return 1  # Actual payout uses bet.potential_win

    def select_winner_by_probability(self, room: GameRoom) -> Optional[str]:
        """Select winner based on configured probabilities."""
        if not room.bet_options:
            return None
        
        probs = [opt.probability for opt in room.bet_options]
        total_prob = sum(probs)
        
        if total_prob == 0:
            winner = random.choice(room.bet_options)
        else:
            normalized = [p / total_prob for p in probs]
            r = random.random()
            cumulative = 0
            winner = room.bet_options[0]
            for i, prob in enumerate(normalized):
                cumulative += prob
                if r <= cumulative:
                    winner = room.bet_options[i]
                    break
        
        return winner.id
