import uuid
import json
import qrcode
import io
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from game_manager import GameManager
from models import GameStatus, WSMessageType

app = FastAPI(title="Live Betting Game API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

game_manager = GameManager()

# room_id -> { player_id/host_id -> WebSocket }
connections: dict[str, dict[str, WebSocket]] = {}


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def broadcast(room_id: str, message: dict, exclude: Optional[str] = None):
    if room_id not in connections:
        return
    dead = []
    for cid, ws in connections[room_id].items():
        if cid == exclude:
            continue
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(cid)
    for cid in dead:
        connections[room_id].pop(cid, None)


async def send_room_state(room_id: str, target_ws: WebSocket):
    state = game_manager.get_room_state(room_id)
    if state:
        await target_ws.send_json({"type": WSMessageType.ROOM_STATE, "data": state})


# ─── REST Endpoints ───────────────────────────────────────────────────────────

class CreateRoomRequest(BaseModel):
    title: str = "Live Betting Game"
    description: str = ""
    bet_options: list[dict] = []


@app.post("/api/rooms")
async def create_room(req: CreateRoomRequest):
    host_id = str(uuid.uuid4())
    room = game_manager.create_room(
        host_id=host_id,
        title=req.title,
        description=req.description,
        bet_options=req.bet_options,
    )
    return {
        "room_id": room.room_id,
        "host_id": host_id,
        "status": room.status,
    }


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    state = game_manager.get_room_state(room_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return state


@app.get("/api/rooms/{room_id}/qr")
async def get_qr(room_id: str, base_url: str = "http://localhost:3000"):
    room = game_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    join_url = f"{base_url}/join/{room_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(join_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    return {"qr_base64": f"data:image/png;base64,{b64}", "join_url": join_url}


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, client_id: str):
    await websocket.accept()

    room_id = room_id.upper()
    if room_id not in connections:
        connections[room_id] = {}
    connections[room_id][client_id] = websocket

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")
            data = msg.get("data", {})

            # ── Player joins ──────────────────────────────────────────────────
            if msg_type == WSMessageType.JOIN:
                name = data.get("name", "Anonymous")
                player = game_manager.add_player(room_id, client_id, name)
                if not player:
                    await websocket.send_json({
                        "type": WSMessageType.ERROR,
                        "data": {"message": "Room is full or not found"}
                    })
                    continue

                # Send full state to the new player
                await send_room_state(room_id, websocket)

                # Notify others
                await broadcast(room_id, {
                    "type": WSMessageType.PLAYER_JOINED,
                    "data": {"player": player.model_dump(), "room_state": game_manager.get_room_state(room_id)}
                }, exclude=client_id)

            # ── Place a bet ───────────────────────────────────────────────────
            elif msg_type == WSMessageType.PLACE_BET:
                option_id = data.get("option_id")
                amount = float(data.get("amount", 0))
                success, message, bet = game_manager.place_bet(room_id, client_id, option_id, amount)

                if not success:
                    await websocket.send_json({
                        "type": WSMessageType.ERROR,
                        "data": {"message": message}
                    })
                    continue

                state = game_manager.get_room_state(room_id)
                await broadcast(room_id, {
                    "type": WSMessageType.BET_PLACED,
                    "data": {"bet": bet.model_dump(), "room_state": state}
                })

            # ── Host actions ──────────────────────────────────────────────────
            elif msg_type == WSMessageType.HOST_ACTION:
                action = data.get("action")
                room = game_manager.get_room(room_id)

                if not room or room.host_id != client_id:
                    await websocket.send_json({
                        "type": WSMessageType.ERROR,
                        "data": {"message": "Not authorized as host"}
                    })
                    continue

                if action == "open_bets":
                    game_manager.update_game_status(room_id, GameStatus.OPEN, client_id)
                elif action == "lock_bets":
                    game_manager.update_game_status(room_id, GameStatus.LOCKED, client_id)
                elif action == "set_winner":
                    option_id = data.get("option_id")
                    success, msg_text = game_manager.set_winner(room_id, option_id, client_id)
                    if not success:
                        await websocket.send_json({
                            "type": WSMessageType.ERROR,
                            "data": {"message": msg_text}
                        })
                        continue
                elif action == "update_options":
                    options = data.get("bet_options", [])
                    game_manager.update_bet_options(room_id, options, client_id)
                elif action == "reset":
                    game_manager.update_game_status(room_id, GameStatus.WAITING, client_id)
                    room2 = game_manager.get_room(room_id)
                    if room2:
                        room2.bets = []
                        room2.winner_option_id = None
                        for p in room2.players.values():
                            p.balance = 1000.0

                state = game_manager.get_room_state(room_id)
                await broadcast(room_id, {
                    "type": WSMessageType.GAME_UPDATED,
                    "data": {"room_state": state}
                })

    except WebSocketDisconnect:
        connections[room_id].pop(client_id, None)
        game_manager.remove_player(room_id, client_id)
        state = game_manager.get_room_state(room_id)
        if state:
            await broadcast(room_id, {
                "type": WSMessageType.PLAYER_LEFT,
                "data": {"player_id": client_id, "room_state": state}
            })
    except Exception as e:
        connections[room_id].pop(client_id, None)
        print(f"WebSocket error for {client_id}: {e}")
