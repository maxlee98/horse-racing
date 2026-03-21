# Phase 2: API and WebSocket Refactoring

## Overview

Phase 2 updates `main.py` to use the new modular service layer and extracts the WebSocket management into a dedicated class.

## Changes Made

### 1. WebSocket Manager (`infrastructure/websocket_manager.py`)

Extracted connection management from inline code to a dedicated class:

```python
class WebSocketManager:
    """Manages WebSocket connections for game rooms."""
    
    def connect(self, room_id: str, client_id: str, websocket: WebSocket)
    def disconnect(self, room_id: str, client_id: str)
    async def broadcast(self, room_id: str, message: dict, exclude: Optional[str])
    async def send_to_client(self, room_id: str, client_id: str, message: dict)
```

**Benefits:**
- Clean separation of WebSocket concerns
- Easier to test (can mock WebSocketManager)
- Supports future features like direct messaging

### 2. Updated `main.py`

**Before:**
```python
from game_manager import GameManager
from models import GameStatus, WSMessageType, GameMode

game_manager = GameManager()
connections: dict[str, dict[str, WebSocket]] = {}

async def broadcast(room_id: str, message: dict, exclude: Optional[str] = None):
    # inline broadcast logic
```

**After:**
```python
from core.models import GameStatus, WSMessageType, GameMode
from core.exceptions import RoomNotFoundException, NotAuthorizedException
from repositories import InMemoryRoomRepository
from services import RoomService, BettingService, PlayerService
from infrastructure import WebSocketManager
from game_modes import get_game_mode

# Infrastructure
repository = InMemoryRoomRepository()
ws_manager = WebSocketManager()

# Services with dependency injection
room_service = RoomService(repository)
betting_service = BettingService(room_service)
player_service = PlayerService(room_service)
```

### 3. Exception Handling

Replaced tuple-based error handling with proper exceptions:

**Before:**
```python
success, message = game_manager.place_bet(...)
if not success:
    # handle error
```

**After:**
```python
try:
    bet = betting_service.place_bet(...)
except InvalidBetException as e:
    # handle error
```

### 4. Host Action Handler

Extracted host action handling to a dedicated function:

```python
async def _handle_host_action(
    room_id: str,
    host_id: str,
    action: str,
    data: dict,
    websocket: WebSocket,
    broadcast_room_state
):
    """Handle host actions with appropriate responses."""
```

This makes the WebSocket endpoint cleaner and easier to maintain.

## New Endpoints

Added a health check endpoint:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "active_rooms": len(repository.list_all()),
        "active_connections": ...,
    }
```

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│           main.py (API Layer)           │
│  - REST endpoints                       │
│  - WebSocket endpoint                   │
│  - Exception handling                   │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌─────────┐   ┌──────────┐   ┌──────────┐
│ Services│   │Game Modes│   │Infrastructure│
│         │   │          │   │              │
│- Room   │   │- Standard│   │- WebSocket   │
│- Betting│   │- Roulette│   │  Manager     │
│- Player │   │- Racing  │   │              │
└─────────┘   └──────────┘   └──────────┘
    │
    ▼
┌─────────────┐
│ Repositories│
│             │
│ - In-Memory │
│ - (Redis)   │
└─────────────┘
```

## Benefits

1. **Cleaner main.py**: Reduced from ~300 lines to ~200 lines with clear separation
2. **Type Safety**: Proper type hints throughout
3. **Better Error Handling**: Exceptions instead of tuple returns
4. **Testability**: Each component can be mocked
5. **API Documentation**: FastAPI auto-generates docs at `/docs`

## Testing

The refactored code was verified with:

```python
# Create room
room = room_service.create_room(
    host_id='test-host',
    title='Test Room',
    bet_options=[{'id': '1', 'label': 'Option 1', 'odds': 2.0}],
    game_mode=GameMode.STANDARD
)

# Output: ✅ Room created successfully: 54EEA34A
```

## Backwards Compatibility

The API endpoints remain unchanged:
- `POST /api/rooms` - Create room
- `GET /api/rooms/{room_id}` - Get room state
- `GET /api/rooms/{room_id}/qr` - Generate QR code
- `POST /api/rooms/{room_id}/probabilities` - Update probabilities
- `WS /ws/{room_id}/{client_id}` - WebSocket connection

WebSocket message types are unchanged, ensuring frontend compatibility.

## Next Steps

1. **Phase 3**: Frontend feature-based reorganization
2. **Phase 4**: Shared constants strategy
3. **Phase 5**: Unit tests for services
4. **Phase 6**: Redis repository implementation
