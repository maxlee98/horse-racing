from pydantic import BaseModel
from typing import Optional
from enum import Enum


class GameStatus(str, Enum):
    WAITING = "waiting"
    OPEN = "open"       # Bets are open
    LOCKED = "locked"   # Bets locked, game in progress
    ENDED = "ended"     # Game over, results out


class BetOption(BaseModel):
    id: str
    label: str
    odds: float = 2.0


class Player(BaseModel):
    id: str
    name: str
    balance: float = 1000.0
    is_connected: bool = True


class Bet(BaseModel):
    player_id: str
    player_name: str
    option_id: str
    option_label: str
    amount: float
    potential_win: float


class GameRoom(BaseModel):
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


# WebSocket message types
class WSMessageType(str, Enum):
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
