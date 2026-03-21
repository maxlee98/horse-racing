# Phase 1: Backend Service Layer - Migration Guide

## Overview

This document describes the modularization of the backend from a monolithic `game_manager.py` into a clean, service-oriented architecture.

## Before vs After

### Before (Monolithic)
```
backend/
├── models.py          # ~100 lines - Data models
├── game_manager.py    # ~900 lines - ALL business logic
└── main.py           # ~200 lines - API + WebSocket handling
```

### After (Modular)
```
backend/
├── core/                    # Domain models
│   ├── models.py           # Pydantic models
│   └── exceptions.py       # Custom exceptions
├── repositories/           # Data access
│   ├── base.py            # Repository interface
│   └── memory.py          # In-memory implementation
├── game_modes/            # Strategy pattern for games
│   ├── base.py            # Abstract strategy
│   ├── standard.py        # Standard betting
│   ├── roulette.py        # Roulette game
│   └── horse_racing.py    # Horse racing
├── services/              # Business logic
│   ├── room_service.py    # Room management
│   ├── betting_service.py # Bet operations
│   └── player_service.py  # Player management
└── main.py               # Thin API layer
```

## Architecture Benefits

### 1. Single Responsibility Principle
Each module has a single, well-defined responsibility:
- **RoomService**: Room lifecycle (create, update, delete)
- **BettingService**: Bet placement and payouts
- **PlayerService**: Player management
- **GameModeStrategy**: Game-specific logic (animations, win conditions)
- **RoomRepository**: Data persistence abstraction

### 2. Strategy Pattern for Game Modes
New game modes can be added without modifying existing code:

```python
class MyNewGame(GameModeStrategy):
    @property
    def name(self) -> str:
        return "my_new_game"
    
    def calculate_probabilities(self, room: GameRoom) -> None:
        # Game-specific probability logic
        pass
    
    async def run_animation(self, room, broadcast):
        # Game-specific animation
        pass
```

Register in `game_modes/__init__.py`:
```python
GAME_MODES = {
    "standard": StandardGameMode,
    "horse_racing": HorseRacingMode,
    "roulette": RouletteMode,
    "my_new_game": MyNewGame,  # Add here
}
```

### 3. Repository Pattern for Persistence
The `RoomRepository` abstraction allows switching storage backends:

```python
# Current: In-memory
repository = InMemoryRoomRepository()

# Future: Redis
# repository = RedisRoomRepository(redis_url="redis://localhost")

# Future: PostgreSQL
# repository = PostgresRoomRepository(db_url="postgresql://...")
```

### 4. Easier Testing
Each service can be unit tested in isolation:

```python
def test_betting_service():
    repo = InMemoryRoomRepository()
    room_service = RoomService(repo)
    betting_service = BettingService(room_service)
    
    # Create room and player
    room = room_service.create_room(...)
    player = PlayerService(room_service).add_player(...)
    
    # Test bet placement
    bet = betting_service.place_bet(room_id, player_id, option_id, 100)
    assert bet.amount == 100
```

## Key Design Decisions

### 1. Game Mode Strategy Pattern
**Why**: Different game modes (roulette, horse racing, standard) have different:
- Animation sequences
- Win condition checking
- Probability calculations
- Payout rules

**Benefit**: Adding a new game mode requires only creating a new strategy class, not modifying existing code (Open/Closed Principle).

### 2. Service Dependencies
Services depend on each other through constructor injection:

```python
class BettingService:
    def __init__(self, room_service: RoomService):
        self._room_service = room_service
```

This makes dependencies explicit and enables mocking for testing.

### 3. Exception Hierarchy
Custom exceptions provide clear error semantics:

```python
class GameException(Exception):
    """Base game exception"""
    pass

class RoomNotFoundException(GameException):
    """Room doesn't exist"""
    pass

class NotAuthorizedException(GameException):
    """User can't perform action"""
    pass
```

## Migration Path

### Step 1: Copy Existing Logic
- [x] Extract models to `core/models.py`
- [x] Move roulette logic to `game_modes/roulette.py`
- [x] Move horse racing logic to `game_modes/horse_racing.py`
- [x] Split game_manager methods into services

### Step 2: Update main.py (Phase 2)
The main.py file will be refactored in Phase 2 to use the new services:

```python
# Before
game_manager = GameManager()

# After
repository = InMemoryRoomRepository()
room_service = RoomService(repository)
betting_service = BettingService(room_service)
player_service = PlayerService(room_service)
```

## File Structure Details

### core/models.py
Contains all Pydantic models:
- `GameRoom`: Main room state
- `Player`: Player data
- `Bet`: Bet data
- `BetOption`: Betting option
- Enums: `GameStatus`, `GameMode`, `RouletteBetType`, `WSMessageType`

### game_modes/
Each game mode implements `GameModeStrategy`:
- `calculate_probabilities()`: Set win probabilities
- `run_animation()`: Run the game animation
- `check_win()`: Determine if a bet wins
- `get_payout_multiplier()`: Calculate payout

### services/
- **RoomService**: Room CRUD, status management, winner selection
- **BettingService**: Bet placement, payout processing
- **PlayerService**: Add/remove players, balance management

### repositories/
- **RoomRepository**: Abstract interface
- **InMemoryRoomRepository**: Dictionary-based storage

## Next Steps

1. **Phase 2**: Update `main.py` to use services
2. **Phase 3**: Add WebSocket manager abstraction
3. **Phase 4**: Create API route modules
4. **Phase 5**: Add unit tests for services
5. **Phase 6**: Create Redis repository implementation

## Backwards Compatibility

The old `game_manager.py` and `models.py` files are kept in place temporarily. Once all phases are complete, they will be removed.
