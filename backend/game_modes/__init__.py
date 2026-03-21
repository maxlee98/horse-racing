"""Game mode implementations using the Strategy pattern."""

from .base import GameModeStrategy
from .standard import StandardGameMode
from .horse_racing import HorseRacingMode
from .roulette import RouletteMode

__all__ = [
    "GameModeStrategy",
    "StandardGameMode",
    "HorseRacingMode",
    "RouletteMode",
]

# Factory for creating game mode instances
GAME_MODES: dict[str, type[GameModeStrategy]] = {
    "standard": StandardGameMode,
    "horse_racing": HorseRacingMode,
    "roulette": RouletteMode,
}


def get_game_mode(mode: str) -> GameModeStrategy:
    """Get a game mode strategy by name."""
    if mode not in GAME_MODES:
        raise ValueError(f"Unknown game mode: {mode}")
    return GAME_MODES[mode]()
