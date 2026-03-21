# Phase 4: Shared Constants Strategy

## Overview

Established a single source of truth for game configuration constants shared between frontend and backend, eliminating duplication and synchronization issues.

## Problem

Constants were defined in multiple places:
- **Backend**: `game_modes/roulette.py` had `ROULETTE_COLORS`, `ROULETTE_WHEEL_ORDER`
- **Frontend**: `shared/types/game.ts` had duplicate `ROULETTE_COLORS`, `ROULETTE_WHEEL_ORDER`
- **Frontend**: `shared/lib/constants.ts` had `GAME_PRESETS` for UI
- **Backend**: `game_modes/roulette.py` had `ROULETTE_PAYOUTS`

**Risk**: Changing a constant in one place but not the other leads to bugs.

## Solution

### 1. Centralized Constants Class (Backend)

Created `backend/core/constants.py`:

```python
class GameConstants:
    """Game configuration constants - single source of truth."""
    
    # Roulette
    ROULETTE_WHEEL_ORDER: List[int] = [...]
    ROULETTE_COLORS: Dict[int, str] = {...}
    ROULETTE_PAYOUTS: Dict[str, int] = {...}
    
    # Game presets
    GAME_PRESETS: Dict[str, Dict[str, Any]] = {...}
    
    # Configuration
    MAX_PLAYERS: int = 8
    DEFAULT_BALANCE: float = 1000.0
    QUICK_BET_AMOUNTS: List[int] = [50, 100, 200, 500]
```

### 2. API Endpoint for Frontend Sync

Added to `main.py`:

```python
@app.get("/api/constants")
async def get_constants():
    """Get shared game constants for frontend synchronization."""
    return GameConstants.to_dict()
```

Response format:
```json
{
  "roulette": {
    "wheel_order": [0, 28, 9, ...],
    "colors": { "0": "green", "1": "red", ... },
    "payouts": { "single": 35, "red": 1, ... }
  },
  "game_presets": {
    "standard": { ... },
    "horse_racing": { ... },
    "roulette": { ... }
  },
  "quick_bet_amounts": [50, 100, 200, 500],
  "max_players": 8,
  "default_balance": 1000.0
}
```

### 3. Frontend Fallback Constants

Updated `frontend/src/shared/lib/constants.ts`:

```typescript
// Fallback constants (used before API fetch or if fetch fails)
export const FALLBACK_CONSTANTS = { ... };

// API method to fetch server constants
export const api = {
  async getConstants() {
    const res = await fetch(`${API_BASE}/api/constants`);
    return res.json();
  },
};
```

## Updated Game Mode to Use Centralized Constants

Modified `backend/game_modes/roulette.py`:

```python
from core.constants import GameConstants

# Import constants from centralized location
AMERICAN_ROULETTE_ORDER = GameConstants.ROULETTE_WHEEL_ORDER
ROULETTE_COLORS = GameConstants.ROULETTE_COLORS
ROULETTE_PAYOUTS = {
    RouletteBetType.SINGLE: GameConstants.ROULETTE_PAYOUTS["single"],
    RouletteBetType.RED: GameConstants.ROULETTE_PAYOUTS["red"],
    # ... etc
}
```

## Benefits

1. **Single Source of Truth**: Change in one place, reflects everywhere
2. **API Synchronization**: Frontend fetches constants on load
3. **Fallback Support**: Frontend has fallback values if API fails
4. **Type Safety**: TypeScript types match Python types
5. **Documentation**: Each constant is documented in one place

## Usage

### Backend (Python)
```python
from core.constants import GameConstants

# Use constants directly
wheel_order = GameConstants.ROULETTE_WHEEL_ORDER
max_players = GameConstants.MAX_PLAYERS
```

### Frontend (TypeScript)
```typescript
import { api } from '@/shared/lib/api';

// Fetch from API (recommended)
const constants = await api.getConstants();

// Or use fallback
import { FALLBACK_CONSTANTS } from '@/shared/lib/constants';
const wheelOrder = FALLBACK_CONSTANTS.roulette.wheel_order;
```

## Migration Path

### Completed ✅
- [x] Created `backend/core/constants.py` with all constants
- [x] Added `/api/constants` endpoint
- [x] Updated `frontend/src/shared/lib/api.ts` with `getConstants()`
- [x] Updated `frontend/src/shared/lib/constants.ts` with fallbacks
- [x] Updated `backend/game_modes/roulette.py` to use centralized constants

### Future Improvements
- [ ] Add React context/provider for constants
- [ ] Fetch constants on app initialization
- [ ] Add constant validation (e.g., wheel order has 38 numbers)
- [ ] Add versioning for constants

## Files Changed

| File | Change |
|------|--------|
| `backend/core/constants.py` | **NEW** - Centralized constants class |
| `backend/main.py` | Added `/api/constants` endpoint |
| `backend/game_modes/roulette.py` | Uses `GameConstants` instead of inline |
| `frontend/src/shared/lib/api.ts` | Added `getConstants()` method |
| `frontend/src/shared/lib/constants.ts` | Added `FALLBACK_CONSTANTS` |

## Next Steps

1. **Phase 5**: Unit tests for services
2. **Phase 6**: Redis repository implementation
3. **Future**: Code generation to auto-sync TypeScript types from Python
