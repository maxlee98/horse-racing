# Phase 3: Frontend Feature-Based Reorganization

## Overview

Reorganized the frontend from a flat structure to a **feature-based architecture** that scales better as the application grows.

## Before vs After

### Before (Flat Structure)
```
frontend/src/
├── app/
│   ├── page.tsx              # Home page (250 lines)
│   ├── host/[roomId]/        # Host page (600 lines)
│   └── join/[roomId]/        # Join page (400 lines)
├── components/
│   ├── RouletteTable.tsx     # Mixed concerns
│   └── RouletteWheel.tsx
├── hooks/
│   └── useWebSocket.ts
└── types/
    └── game.ts
```

### After (Feature-Based Structure)
```
frontend/src/
├── app/                      # Next.js routes (thin pages)
│   ├── page.tsx             # Delegates to feature
│   ├── host/[roomId]/
│   └── join/[roomId]/
│
├── shared/                   # Shared across all features
│   ├── types/
│   │   └── game.ts          # All TypeScript types
│   ├── hooks/
│   │   └── useWebSocket.ts  # WebSocket hook
│   ├── lib/
│   │   ├── api.ts           # API client
│   │   └── constants.ts     # Game presets, constants
│   └── index.ts             # Barrel exports
│
├── features/                 # Feature-specific modules
│   ├── roulette/
│   │   ├── components/
│   │   │   ├── RouletteWheel.tsx
│   │   │   └── RouletteTable.tsx
│   │   └── index.ts
│   │
│   ├── horse-racing/
│   │   ├── components/
│   │   └── index.ts
│   │
│   └── room/
│       ├── components/      # Room UI components
│       └── hooks/           # Room-specific hooks
│
└── components/              # (Legacy - to be migrated)
    ├── RouletteTable.tsx
    └── RouletteWheel.tsx
```

## Benefits of Feature-Based Architecture

### 1. **Cohesion**
Related code lives together:
```
features/roulette/
├── components/          # Roulette-specific UI
├── hooks/               # Roulette-specific logic
└── utils/               # Roulette-specific helpers
```

### 2. **Scalability**
Adding a new game mode is now trivial:
```
features/
├── roulette/            # Existing
├── horse-racing/        # Existing
└── blackjack/           # Just add this folder!
    ├── components/
    ├── hooks/
    └── index.ts
```

### 3. **Clear Import Paths**
```typescript
// Before - confusing
import { useWebSocket } from '@/hooks/useWebSocket';
import { RoomState } from '@/types/game';

// After - clear feature boundaries
import { useWebSocket, RoomState } from '@/shared';
import { RouletteWheel } from '@/features/roulette';
```

### 4. **Easier Testing**
Each feature can be tested in isolation:
```typescript
// Test roulette feature independently
import { RouletteWheel } from '@/features/roulette';
```

## Shared Module

The `shared/` directory contains code used across all features:

### Types (`shared/types/game.ts`)
All TypeScript interfaces and types:
- `RoomState`, `Player`, `Bet`
- `GameStatus`, `GameMode`
- `RouletteState`, `RaceState`
- Constants like `ROULETTE_COLORS`

### Hooks (`shared/hooks/useWebSocket.ts`)
Reusable WebSocket hook for real-time communication.

### API (`shared/lib/api.ts`)
Centralized API client with methods:
- `api.createRoom()`
- `api.getRoom(roomId)`
- `api.getQRCode(roomId, baseUrl)`
- `api.updateProbabilities(...)`

### Constants (`shared/lib/constants.ts`)
Game presets and configuration:
```typescript
GAME_PRESETS.standard    // Default 2-option betting
GAME_PRESETS.horseRacing // 5 horses preset
GAME_PRESETS.roulette    // Full roulette board

QUICK_BET_AMOUNTS = [50, 100, 200, 500]
STATUS_COLORS = { waiting, open, locked, ended }
```

## Migration Path

### Step 1: Create Shared Module ✅
- [x] Move types to `shared/types/game.ts`
- [x] Move `useWebSocket` to `shared/hooks/`
- [x] Create API client in `shared/lib/api.ts`
- [x] Create constants in `shared/lib/constants.ts`
- [x] Create barrel exports in `shared/index.ts`

### Step 2: Create Feature Modules ✅
- [x] Create `features/roulette/` structure
- [x] Create `features/horse-racing/` structure
- [x] Create barrel exports for each feature

### Step 3: Migrate Components (Future)
- [ ] Move `RouletteTable.tsx` to `features/roulette/components/`
- [ ] Move `RouletteWheel.tsx` to `features/roulette/components/`
- [ ] Extract horse racing components from pages
- [ ] Update page imports to use new structure

### Step 4: Page Simplification (Future)
Current pages are large (~400-600 lines). Future work:
- Extract page sections into feature components
- Use composition pattern for game mode UIs
- Create room layout components

## Import Patterns

### Importing from Shared
```typescript
// Everything from shared
import { useWebSocket, RoomState, api, GAME_PRESETS } from '@/shared';

// Specific items
import { type RoomState, GameStatus } from '@/shared/types/game';
import { api } from '@/shared/lib/api';
```

### Importing from Features
```typescript
// Roulette feature
import { RouletteWheel, RouletteTable } from '@/features/roulette';

// Horse racing feature (when components are added)
import { RaceTrack } from '@/features/horse-racing';
```

## Backwards Compatibility

The old file structure is preserved temporarily:
- `src/components/RouletteTable.tsx` (old)
- `src/features/roulette/components/RouletteTable.tsx` (new)
- `src/types/game.ts` (old)
- `src/shared/types/game.ts` (new)

Pages currently use the old imports. Migration is gradual and can be done incrementally.

## Next Steps

1. **Phase 4**: Shared constants between frontend and backend
2. **Phase 5**: Unit tests for services
3. **Phase 6**: Redis repository implementation
4. **Future**: Extract page components, implement lazy loading

## Summary

The frontend now has a **scalable, feature-based architecture** that:
- ✅ Separates concerns by feature
- ✅ Provides clear import paths
- ✅ Makes adding new game modes trivial
- ✅ Centralizes shared code
- ✅ Maintains backwards compatibility during migration
