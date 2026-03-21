"""Shared constants between frontend and backend.

This module contains game configuration constants that need to be
synchronized between the backend (Python) and frontend (TypeScript).

When adding new constants, consider:
1. Backend uses these directly
2. Frontend fetches via /api/constants endpoint
3. Document the constant's purpose for both sides
"""

from typing import Dict, List, Any


class GameConstants:
    """Game configuration constants."""

    # American Roulette wheel order (clockwise from 0)
    # 37 represents 00 for calculations
    ROULETTE_WHEEL_ORDER: List[int] = [
        0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1,
        37,  # 00
        27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16, 4, 23, 35, 14, 2
    ]

    # Number colors (0 and 37/00 are green)
    ROULETTE_COLORS: Dict[int, str] = {
        0: "green",
        37: "green",  # 00
        # Red numbers
        1: "red", 3: "red", 5: "red", 7: "red", 9: "red",
        12: "red", 14: "red", 16: "red", 18: "red",
        19: "red", 21: "red", 23: "red", 25: "red", 27: "red",
        30: "red", 32: "red", 34: "red", 36: "red",
        # Black numbers
        2: "black", 4: "black", 6: "black", 8: "black", 10: "black",
        11: "black", 13: "black", 15: "black", 17: "black",
        20: "black", 22: "black", 24: "black", 26: "black", 28: "black",
        29: "black", 31: "black", 33: "black", 35: "black"
    }

    # Roulette bet type payouts (x:1)
    ROULETTE_PAYOUTS: Dict[str, int] = {
        "single": 35,
        "red": 1,
        "black": 1,
        "even": 1,
        "odd": 1,
        "low": 1,
        "high": 1,
        "first_dozen": 2,
        "second_dozen": 2,
        "third_dozen": 2,
        "first_column": 2,
        "second_column": 2,
        "third_column": 2,
    }

    # Game mode presets
    GAME_PRESETS: Dict[str, Dict[str, Any]] = {
        "standard": {
            "title": "",
            "description": "",
            "options": [
                {"id": "1", "label": "Team A", "odds": 1.8},
                {"id": "2", "label": "Team B", "odds": 2.1},
            ],
            "use_randomized_probabilities": False,
        },
        "horse_racing": {
            "title": "🏇 Horse Racing",
            "description": "Watch the horses race to the finish line!",
            "options": [
                {"id": "1", "label": "🐎 Thunder Bolt", "odds": 2.5},
                {"id": "2", "label": "🐎 Midnight Runner", "odds": 3.0},
                {"id": "3", "label": "🐎 Golden Mane", "odds": 2.0},
                {"id": "4", "label": "🐎 Silver Streak", "odds": 4.0},
                {"id": "5", "label": "🐎 Wild Spirit", "odds": 3.5},
            ],
            "use_randomized_probabilities": True,
        },
        "roulette": {
            "title": "🎰 Roulette",
            "description": "American Roulette with 38 pockets (0, 00, 1-36)",
            "options": [
                # Individual numbers
                {"id": "0", "label": "0", "odds": 36},
                {"id": "00", "label": "00", "odds": 36},
                *[
                    {"id": str(i), "label": str(i), "odds": 36}
                    for i in range(1, 37)
                ],
                # Even money bets
                {"id": "red", "label": "Red", "odds": 2},
                {"id": "black", "label": "Black", "odds": 2},
                {"id": "even", "label": "Even", "odds": 2},
                {"id": "odd", "label": "Odd", "odds": 2},
                {"id": "1-18", "label": "1-18 (Low)", "odds": 2},
                {"id": "19-36", "label": "19-36 (High)", "odds": 2},
                # Dozens
                {"id": "1st12", "label": "1st 12", "odds": 3},
                {"id": "2nd12", "label": "2nd 12", "odds": 3},
                {"id": "3rd12", "label": "3rd 12", "odds": 3},
                # Columns
                {"id": "col1", "label": "Column 1", "odds": 3},
                {"id": "col2", "label": "Column 2", "odds": 3},
                {"id": "col3", "label": "Column 3", "odds": 3},
            ],
            "use_randomized_probabilities": False,
        },
    }

    # Quick bet amounts (for UI buttons)
    QUICK_BET_AMOUNTS: List[int] = [50, 100, 200, 500]

    # Game configuration
    MAX_PLAYERS: int = 8
    DEFAULT_BALANCE: float = 1000.0

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Export all constants as a dictionary for API response."""
        return {
            "roulette": {
                "wheel_order": cls.ROULETTE_WHEEL_ORDER,
                "colors": cls.ROULETTE_COLORS,
                "payouts": cls.ROULETTE_PAYOUTS,
            },
            "game_presets": cls.GAME_PRESETS,
            "quick_bet_amounts": cls.QUICK_BET_AMOUNTS,
            "max_players": cls.MAX_PLAYERS,
            "default_balance": cls.DEFAULT_BALANCE,
        }
