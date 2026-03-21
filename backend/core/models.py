"""Core domain models for the betting game."""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class GameStatus(str, Enum):
    """Game status states."""
    WAITING = "waiting"
    OPEN = "open"       # Bets are open
    LOCKED = "locked"   # Bets locked, game in progress
    ENDED = "ended"     # Game over, results out


class BetOption(BaseModel):
    """A betting option (e.g., a horse, a team, a number)."""
    id: str
    label: str
    odds: float = 2.0
    probability: float = 0.5  # Win probability (0-1), used for randomized winner selection


class GameMode(str, Enum):
    """Available game modes."""
    STANDARD = "standard"
    HORSE_RACING = "horse_racing"
    ROULETTE = "roulette"


class RouletteBetType(str, Enum):
    """Types of roulette bets."""
    SINGLE = "single"           # Single number (0, 00, 1-36)
    RED = "red"                 # All red numbers
    BLACK = "black"             # All black numbers
    EVEN = "even"               # Even numbers (2, 4, 6... excludes 0, 00)
    ODD = "odd"                 # Odd numbers (1, 3, 5... excludes 0, 00)
    LOW = "low"                 # 1-18
    HIGH = "high"               # 19-36
    FIRST_DOZEN = "first_dozen"     # 1-12
    SECOND_DOZEN = "second_dozen"   # 13-24
    THIRD_DOZEN = "third_dozen"     # 25-36
    FIRST_COLUMN = "first_column"   # 1, 4, 7, 10...
    SECOND_COLUMN = "second_column" # 2, 5, 8, 11...
    THIRD_COLUMN = "third_column"   # 3, 6, 9, 12...


class Player(BaseModel):
    """A player in the game."""
    id: str
    name: str
    balance: float = 1000.0
    is_connected: bool = True


class Bet(BaseModel):
    """A bet placed by a player."""
    player_id: str
    player_name: str
    option_id: str
    option_label: str
    amount: float
    potential_win: float
    bet_type: Optional[RouletteBetType] = None  # For roulette mode
    bet_number: Optional[int] = None  # For single number bets in roulette


class GameRoom(BaseModel):
    """A game room containing all game state."""
    room_id: str
    host_id: str
    status: GameStatus = GameStatus.WAITING
    title: str = "Live Betting Game"
    description: str = ""
    bet_options: list[BetOption] = []
    players: dict[str, Player] = {}
    bets: list[Bet] = []
    winner_option_id: Optional[str] = None
    max_players: int = 8
    game_mode: GameMode = GameMode.STANDARD
    round_number: int = 1
    use_randomized_probabilities: bool = False  # Whether to use probability-based winner selection


class WSMessageType(str, Enum):
    """WebSocket message types."""
    # Client -> Server
    JOIN = "join"
    PLACE_BET = "place_bet"
    HOST_ACTION = "host_action"

    # Server -> Client
    ROOM_STATE = "room_state"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    BET_PLACED = "bet_placed"
    GAME_UPDATED = "game_updated"
    GAME_ENDED = "game_ended"
    ERROR = "error"
    RACE_STARTED = "race_started"  # For horse racing mode
    RACE_PROGRESS = "race_progress"  # Race animation updates
    RACE_ENDED = "race_ended"  # Race finished with winner
    ROULETTE_STARTED = "roulette_started"
    ROULETTE_PROGRESS = "roulette_progress"
    ROULETTE_BALL_SETTLING = "roulette_ball_settling"
    ROULETTE_ENDED = "roulette_ended"
    ROULETTE_REVEALED = "roulette_revealed"  # Host clicked Close, reveal results to players
