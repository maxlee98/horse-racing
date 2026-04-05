# 🎲 BetLive — Real-Time Multiplayer Betting Game

A live betting platform supporting up to 8 players. Players scan a QR code to join, place bets in real-time, and see results instantly via WebSockets.

---

## 🗂 Project Structure

```
betting-game/
├── backend/              # Python FastAPI + WebSockets
│   ├── main.py           # App entry point, REST + WS endpoints
│   ├── core/             # Domain models and business logic
│   │   ├── models.py     # Pydantic data models (GameRoom, Player, Bet, etc.)
│   │   ├── constants.py  # Shared game constants
│   │   └── exceptions.py # Custom exceptions
│   ├── services/         # Service layer (business logic)
│   │   ├── room_service.py
│   │   ├── betting_service.py
│   │   └── player_service.py
│   ├── repositories/     # Data access abstraction
│   │   └── memory.py     # In-memory storage
│   ├── game_modes/       # Game mode strategies (Strategy pattern)
│   │   ├── standard.py
│   │   ├── horse_racing.py
│   │   └── roulette.py
│   ├── infrastructure/   # External concerns
│   │   └── websocket_manager.py
│   └── requirements.txt
└── frontend/             # Next.js 14 + TypeScript + Tailwind
    └── src/
        ├── app/
        │   ├── page.tsx              # Host: Create a game
        │   ├── host/[roomId]/        # Host: Control panel + QR
        │   └── join/[roomId]/        # Player: Betting page
        ├── shared/           # Shared utilities
        │   ├── types/game.ts         # TypeScript types
        │   ├── hooks/useWebSocket.ts # WS connection hook
        │   ├── lib/api.ts            # API client
        │   └── lib/constants.ts      # Constants
        └── components/               # Reusable components
            ├── RouletteWheel.tsx
            └── RouletteTable.tsx
```

---

## 🎮 Game Modes

| Mode | Description |
|------|-------------|
| **Standard** | Simple betting where host manually declares winner |
| **Horse Racing** | Animated race with momentum mechanics. Winner based on race finish |
| **Roulette** | American Roulette (38 pockets) with spinning wheel animation |

---

## 🚀 Quick Start

### 1. Backend (Python FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

---

## 🎮 How to Play

### Host Flow
1. Go to **http://localhost:3000**
2. Enter a game title and select a game mode
3. Click **Create Game Room**
4. You'll be taken to the **Host Control Panel** with a QR code
5. Share the QR code or link with players (up to 8)
6. Click **Open Betting** to let players place bets
7. Click **Lock Bets** when ready
8. **Declare the Winner** — payouts happen automatically!
9. Click **Next Round** to play again

### Player Flow
1. Scan the QR code (or open the join link)
2. Enter your name
3. Select a bet option and amount
4. Watch live updates as other players bet
5. See your result when the host declares a winner

---

## 🔌 API Endpoints

| Method | Endpoint                    | Description            |
| ------ | --------------------------- | ---------------------- |
| POST   | `/api/rooms`                | Create a new game room |
| GET    | `/api/rooms/{room_id}`       | Get current room state  |
| GET    | `/api/rooms/{room_id}/qr`    | Get QR code as base64   |
| POST   | `/api/rooms/{room_id}/probabilities` | Update win probabilities |
| GET    | `/api/constants`            | Get shared game constants |
| WS     | `/ws/{room_id}/{client_id}` | WebSocket connection   |

### WebSocket Message Types

**Client → Server:**
- `join` — `{ name: string }`
- `place_bet` — `{ option_id: string, amount: number, bet_type?: string, bet_number?: number }`
- `host_action` — `{ action: "open_bets" | "lock_bets" | "set_winner" | "next_round" | "reset_lobby" | "change_game" | "randomize_probabilities" | "select_winner_by_probability", option_id?: string, game_mode?: string }`

**Server → Client:**
- `room_state` — Full room snapshot
- `player_joined` / `player_left`
- `bet_placed`
- `game_updated`
- `game_ended`
- `error` — `{ message: string }`
- `race_started` / `race_progress` / `race_ended` — Horse racing animations
- `roulette_started` / `roulette_progress` / `roulette_ball_settling` / `roulette_ended` — Roulette animations
- `game_mode_changed` — Room changed game mode

---

## ⚙️ Configuration

Frontend environment variables (`frontend/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

For production, update these to your server's URL.

---

## 🏗 Tech Stack

| Layer     | Tech                                          |
| --------- | --------------------------------------------- |
| Backend   | Python 3.11, FastAPI, Uvicorn                 |
| Real-time | WebSockets (native FastAPI)                   |
| QR Code   | `qrcode[pil]`                                 |
| Frontend  | Next.js 14, TypeScript                        |
| Styling   | Tailwind CSS                                  |
| State     | In-memory (upgrade to Redis for multi-server) |

---

## 🔮 Future Enhancements

- [ ] Redis for persistent state across restarts
- [ ] Authentication (host password)
- [ ] Animated live odds that shift as bets come in
- [ ] Player avatars / leaderboard
- [ ] Multiple rounds per session
- [ ] Mobile PWA support
