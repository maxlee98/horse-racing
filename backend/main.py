"""Live Betting Game API - Refactored to use service layer."""

import uuid
import io
import base64
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# New modular imports
from core.models import GameStatus, WSMessageType, GameMode
from core.constants import GameConstants
from core.exceptions import (
    GameException,
    RoomNotFoundException,
    NotAuthorizedException,
    InvalidBetException,
    RoomFullException,
)
from repositories import InMemoryRoomRepository
from services import RoomService, BettingService, PlayerService
from infrastructure import WebSocketManager
from game_modes import get_game_mode

# FastAPI app with Swagger docs
app = FastAPI(
    title="Live Betting Game API",
    description="Real-time betting game with multiple game modes",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize infrastructure
repository = InMemoryRoomRepository()
ws_manager = WebSocketManager()

# Initialize services with dependency injection
room_service = RoomService(repository)
betting_service = BettingService(room_service)
player_service = PlayerService(room_service)


# ─── Pydantic Request Models ─────────────────────────────────────────────────

class CreateRoomRequest(BaseModel):
    title: str = "Live Betting Game"
    description: str = ""
    bet_options: list[dict] = []
    game_mode: str = "standard"
    use_randomized_probabilities: bool = False


class UpdateProbabilitiesRequest(BaseModel):
    probabilities: dict[str, float]
    host_id: str


class PlaceBetRequest(BaseModel):
    option_id: str
    amount: float
    bet_type: Optional[str] = None
    bet_number: Optional[int] = None


# ─── REST Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/rooms", response_model=dict)
async def create_room(req: CreateRoomRequest):
    """Create a new game room."""
    host_id = str(uuid.uuid4())
    
    # Map string game_mode to enum
    game_mode_map = {
        "horse_racing": GameMode.HORSE_RACING,
        "roulette": GameMode.ROULETTE,
        "standard": GameMode.STANDARD,
    }
    game_mode = game_mode_map.get(req.game_mode, GameMode.STANDARD)
    
    try:
        room = room_service.create_room(
            host_id=host_id,
            title=req.title,
            description=req.description,
            bet_options=req.bet_options,
            game_mode=game_mode,
            use_randomized_probabilities=req.use_randomized_probabilities,
        )
        return {
            "room_id": room.room_id,
            "host_id": host_id,
            "status": room.status.value,
            "game_mode": room.game_mode.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    """Get room state by ID."""
    try:
        room = room_service.get_room_or_raise(room_id)
        return room_service.to_dict(room)
    except RoomNotFoundException:
        raise HTTPException(status_code=404, detail="Room not found")


@app.get("/api/rooms/{room_id}/qr")
async def get_qr(room_id: str, base_url: str = "http://localhost:3000"):
    """Generate QR code for joining a room."""
    try:
        room = room_service.get_room_or_raise(room_id)
    except RoomNotFoundException:
        raise HTTPException(status_code=404, detail="Room not found")

    import qrcode
    
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


@app.post("/api/rooms/{room_id}/probabilities")
async def update_probabilities(room_id: str, req: UpdateProbabilitiesRequest):
    """Update win probabilities for bet options."""
    try:
        room = room_service.update_probabilities(
            room_id, req.probabilities, req.host_id
        )
        return {"success": True, "room": room_service.to_dict(room)}
    except RoomNotFoundException:
        raise HTTPException(status_code=404, detail="Room not found")
    except NotAuthorizedException as e:
        raise HTTPException(status_code=403, detail=str(e))


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────

@app.websocket("/ws/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, client_id: str):
    """WebSocket endpoint for real-time game communication."""
    await websocket.accept()
    
    room_id = room_id.upper()
    ws_manager.connect(room_id, client_id, websocket)
    
    async def broadcast_room_state(exclude: Optional[str] = None):
        """Broadcast current room state to all clients."""
        room = room_service.get_room(room_id)
        if room:
            await ws_manager.broadcast(
                room_id,
                {"type": WSMessageType.ROOM_STATE, "data": room_service.to_dict(room)},
                exclude=exclude
            )

    try:
        while True:
            import json
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")
            data = msg.get("data", {})

            # ── Player joins ─────────────────────────────────────────────
            if msg_type == WSMessageType.JOIN:
                name = data.get("name", "Anonymous")
                
                try:
                    player = player_service.add_player(room_id, client_id, name)
                except RoomNotFoundException:
                    await websocket.send_json({
                        "type": WSMessageType.ERROR,
                        "data": {"message": "Room not found"}
                    })
                    continue
                except RoomFullException:
                    await websocket.send_json({
                        "type": WSMessageType.ERROR,
                        "data": {"message": "Room is full"}
                    })
                    continue

                # Send full state to the new player
                await broadcast_room_state(exclude=client_id)
                
                # Notify others
                await ws_manager.broadcast(
                    room_id,
                    {
                        "type": WSMessageType.PLAYER_JOINED,
                        "data": {"player": player.model_dump()}
                    },
                    exclude=client_id
                )

            # ── Place a bet ───────────────────────────────────────────────
            elif msg_type == WSMessageType.PLACE_BET:
                option_id = data.get("option_id")
                amount = float(data.get("amount", 0))
                bet_type = data.get("bet_type")
                bet_number = data.get("bet_number")
                
                try:
                    bet = betting_service.place_bet(
                        room_id, client_id, option_id, amount, bet_type, bet_number
                    )
                    
                    await ws_manager.broadcast(room_id, {
                        "type": WSMessageType.BET_PLACED,
                        "data": {"bet": bet.model_dump()}
                    })
                    await broadcast_room_state()
                    
                except (InvalidBetException, RoomNotFoundException) as e:
                    await websocket.send_json({
                        "type": WSMessageType.ERROR,
                        "data": {"message": str(e)}
                    })

            # ── Host actions ───────────────────────────────────────────────
            elif msg_type == WSMessageType.HOST_ACTION:
                action = data.get("action")
                
                try:
                    room = room_service.get_room_or_raise(room_id)
                except RoomNotFoundException:
                    await websocket.send_json({
                        "type": WSMessageType.ERROR,
                        "data": {"message": "Room not found"}
                    })
                    continue

                if room.host_id != client_id:
                    await websocket.send_json({
                        "type": WSMessageType.ERROR,
                        "data": {"message": "Not authorized as host"}
                    })
                    continue

                # Handle host actions
                await _handle_host_action(
                    room_id, client_id, action, data, websocket, broadcast_room_state
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(room_id, client_id)
        player_service.remove_player(room_id, client_id)
        await ws_manager.broadcast(room_id, {
            "type": WSMessageType.PLAYER_LEFT,
            "data": {"player_id": client_id}
        })
        await broadcast_room_state()
    except Exception as e:
        ws_manager.disconnect(room_id, client_id)
        print(f"WebSocket error for {client_id}: {e}")


async def _handle_host_action(
    room_id: str,
    host_id: str,
    action: str,
    data: dict,
    websocket: WebSocket,
    broadcast_room_state
):
    """Handle host actions with appropriate responses."""
    
    if action == "open_bets":
        room_service.update_status(room_id, GameStatus.OPEN, host_id)
        await ws_manager.broadcast(room_id, {
            "type": WSMessageType.GAME_UPDATED,
            "data": {"message": "Bets are now open!"}
        })
        await broadcast_room_state()
    
    elif action == "lock_bets":
        room = room_service.get_room_or_raise(room_id)
        game_mode_strategy = get_game_mode(room.game_mode.value)
        
        # Lock bets first
        room_service.update_status(room_id, GameStatus.LOCKED, host_id)
        await broadcast_room_state()
        
        # Run animation for animated game modes
        if room.game_mode in [GameMode.HORSE_RACING, GameMode.ROULETTE]:
            async def broadcast_with_state(msg: dict):
                await ws_manager.broadcast(room_id, msg)
            
            async def run_animation_and_payout():
                """Run animation and process payouts afterwards."""
                # Run the animation
                success, message, winning_value = await game_mode_strategy.run_animation(
                    room, broadcast_with_state
                )
                
                if success and winning_value is not None:
                    # For roulette, winning_value is a dict with winning data
                    # Extract the winning number for payout processing
                    if isinstance(winning_value, dict):
                        winning_number = winning_value["winning_number_int"]
                        winning_data = winning_value
                    else:
                        winning_number = winning_value
                        winning_data = {"winning_number": str(winning_value)}
                    
                    # Process payouts based on the winning number
                    winning_bets = betting_service.process_payouts(room, winning_number)
                    
                    # For roulette, broadcast roulette_ended with winning_bets and update history
                    if room.game_mode == GameMode.ROULETTE:
                        # Add winning number to history (keep last 10)
                        room.roulette_history.append(winning_data["winning_number"])
                        if len(room.roulette_history) > 10:
                            room.roulette_history = room.roulette_history[-10:]
                        
                        await ws_manager.broadcast(room_id, {
                            "type": WSMessageType.ROULETTE_ENDED,
                            "data": {
                                "winning_number": winning_data["winning_number"],
                                "winning_number_int": winning_data["winning_number_int"],
                                "winning_color": winning_data["winning_color"],
                                "winning_option_id": winning_data["winning_option_id"],
                                "winning_bets": winning_bets,
                            }
                        })
                    
                    # Broadcast game ended with winning bets
                    await ws_manager.broadcast(room_id, {
                        "type": WSMessageType.GAME_ENDED,
                        "data": {
                            "winner_option_id": room.winner_option_id,
                            "winning_value": winning_value,
                            "winning_bets": winning_bets,
                            "message": message
                        }
                    })
                    await broadcast_room_state()
            
            # Run animation asynchronously
            asyncio.create_task(run_animation_and_payout())
        else:
            await ws_manager.broadcast(room_id, {
                "type": WSMessageType.GAME_UPDATED,
                "data": {"message": "Bets locked. Waiting for winner."}
            })
    
    elif action == "set_winner":
        option_id = data.get("option_id")
        if not option_id:
            await websocket.send_json({
                "type": WSMessageType.ERROR,
                "data": {"message": "Missing option_id"}
            })
            return
        room = room_service.set_winner(room_id, option_id, host_id)
        
        # Process payouts
        winning_bets = betting_service.process_payouts(room, option_id)
        
        await ws_manager.broadcast(room_id, {
            "type": WSMessageType.GAME_ENDED,
            "data": {
                "winner_option_id": option_id,
                "winning_bets": winning_bets
            }
        })
        await broadcast_room_state()
    
    elif action == "update_probabilities":
        probabilities = data.get("probabilities", {})
        try:
            room_service.update_probabilities(room_id, probabilities, host_id)
            await broadcast_room_state()
        except NotAuthorizedException as e:
            await websocket.send_json({
                "type": WSMessageType.ERROR,
                "data": {"message": str(e)}
            })
    
    elif action == "randomize_probabilities":
        try:
            room_service.randomize_probabilities(room_id, host_id)
            await broadcast_room_state()
        except NotAuthorizedException as e:
            await websocket.send_json({
                "type": WSMessageType.ERROR,
                "data": {"message": str(e)}
            })
    
    elif action == "next_round":
        try:
            room_service.next_round(room_id, host_id)
            await ws_manager.broadcast(room_id, {
                "type": WSMessageType.GAME_UPDATED,
                "data": {"message": "New round started!"}
            })
            await broadcast_room_state()
        except NotAuthorizedException as e:
            await websocket.send_json({
                "type": WSMessageType.ERROR,
                "data": {"message": str(e)}
            })
    
    elif action == "reset_lobby":
        try:
            room_service.reset_lobby(room_id, host_id)
            await ws_manager.broadcast(room_id, {
                "type": WSMessageType.GAME_UPDATED,
                "data": {"message": "Lobby reset!"}
            })
            await broadcast_room_state()
        except NotAuthorizedException as e:
            await websocket.send_json({
                "type": WSMessageType.ERROR,
                "data": {"message": str(e)}
            })
    
    elif action == "select_winner_by_probability":
        room = room_service.get_room_or_raise(room_id)
        game_mode_strategy = get_game_mode(room.game_mode.value)
        
        # Use the strategy to select winner
        winner_id = game_mode_strategy.select_winner_by_probability(room)
        
        if not winner_id:
            await websocket.send_json({
                "type": WSMessageType.ERROR,
                "data": {"message": "Could not determine winner"}
            })
            return
        
        room = room_service.set_winner(room_id, winner_id, host_id)
        winning_bets = betting_service.process_payouts(room, winner_id)
        
        await ws_manager.broadcast(room_id, {
            "type": WSMessageType.GAME_ENDED,
            "data": {
                "winner_option_id": winner_id,
                "winning_bets": winning_bets
            }
        })
        await broadcast_room_state()

    elif action == "reveal_results":
        # Host clicked Close on roulette outcome screen - reveal results to players
        room = room_service.get_room_or_raise(room_id)
        await ws_manager.broadcast(room_id, {
            "type": WSMessageType.ROULETTE_REVEALED,
            "data": {
                "message": "Results revealed!",
                "room_state": room_service.to_dict(room)
            }
        })


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "active_rooms": len(repository.list_all()),
        "active_connections": sum(
            ws_manager.get_connection_count(rid) 
            for rid in ws_manager.get_room_ids()
        ),
    }


@app.get("/api/constants")
async def get_constants():
    """Get shared game constants for frontend synchronization.
    
    Returns all constants defined in GameConstants class.
    Frontend should fetch this on app initialization.
    """
    return GameConstants.to_dict()
