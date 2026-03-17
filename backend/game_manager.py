import uuid
from typing import Optional
from models import GameRoom, Player, Bet, BetOption, GameStatus


class GameManager:
    def __init__(self):
        self.rooms: dict[str, GameRoom] = {}

    def create_room(self, host_id: str, title: str, description: str, bet_options: list[dict]) -> GameRoom:
        room_id = str(uuid.uuid4())[:8].upper()
        options = [BetOption(**opt) for opt in bet_options] if bet_options else []
        room = GameRoom(
            room_id=room_id,
            host_id=host_id,
            title=title,
            description=description,
            bet_options=options,
        )
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        return self.rooms.get(room_id.upper())

    def add_player(self, room_id: str, player_id: str, name: str) -> Optional[Player]:
        room = self.get_room(room_id)
        if not room:
            return None
        if len(room.players) >= room.max_players and player_id not in room.players:
            return None
        player = Player(id=player_id, name=name)
        room.players[player_id] = player
        return player

    def remove_player(self, room_id: str, player_id: str):
        room = self.get_room(room_id)
        if room and player_id in room.players:
            room.players[player_id].is_connected = False

    def place_bet(self, room_id: str, player_id: str, option_id: str, amount: float) -> tuple[bool, str, Optional[Bet]]:
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found", None
        if room.status != GameStatus.OPEN:
            return False, "Betting is not open", None

        player = room.players.get(player_id)
        if not player:
            return False, "Player not found", None
        if player.balance < amount:
            return False, "Insufficient balance", None
        if amount <= 0:
            return False, "Invalid bet amount", None

        # Check if player already bet on this option
        existing = next((b for b in room.bets if b.player_id == player_id and b.option_id == option_id), None)
        if existing:
            return False, "Already placed a bet on this option", None

        option = next((o for o in room.bet_options if o.id == option_id), None)
        if not option:
            return False, "Invalid option", None

        player.balance -= amount
        bet = Bet(
            player_id=player_id,
            player_name=player.name,
            option_id=option_id,
            option_label=option.label,
            amount=amount,
            potential_win=round(amount * option.odds, 2),
        )
        room.bets.append(bet)
        return True, "Bet placed", bet

    def update_game_status(self, room_id: str, status: GameStatus, host_id: str) -> tuple[bool, str]:
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found"
        if room.host_id != host_id:
            return False, "Not authorized"
        room.status = status
        return True, "Status updated"

    def set_winner(self, room_id: str, option_id: str, host_id: str) -> tuple[bool, str]:
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found"
        if room.host_id != host_id:
            return False, "Not authorized"

        option = next((o for o in room.bet_options if o.id == option_id), None)
        if not option:
            return False, "Invalid option"

        room.winner_option_id = option_id
        room.status = GameStatus.ENDED

        # Pay out winners
        for bet in room.bets:
            if bet.option_id == option_id:
                player = room.players.get(bet.player_id)
                if player:
                    player.balance += bet.potential_win

        return True, "Winner set"

    def update_bet_options(self, room_id: str, bet_options: list[dict], host_id: str) -> tuple[bool, str]:
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found"
        if room.host_id != host_id:
            return False, "Not authorized"
        room.bet_options = [BetOption(**opt) for opt in bet_options]
        return True, "Options updated"

    def get_room_state(self, room_id: str) -> Optional[dict]:
        room = self.get_room(room_id)
        if not room:
            return None
        return {
            "room_id": room.room_id,
            "title": room.title,
            "description": room.description,
            "status": room.status,
            "bet_options": [o.model_dump() for o in room.bet_options],
            "players": {pid: p.model_dump() for pid, p in room.players.items()},
            "bets": [b.model_dump() for b in room.bets],
            "winner_option_id": room.winner_option_id,
            "max_players": room.max_players,
            "player_count": len([p for p in room.players.values() if p.is_connected]),
        }
