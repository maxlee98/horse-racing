"""Betting service for managing bets and payouts."""

from typing import Optional, Callable, Any
from core.models import GameRoom, Bet, Player, GameStatus
from core.exceptions import InvalidBetException, RoomNotFoundException
from game_modes import get_game_mode


class BettingService:
    """Service for placing bets and calculating payouts."""

    def __init__(self, room_service):
        """Initialize with room service."""
        self._room_service = room_service

    def place_bet(
        self,
        room_id: str,
        player_id: str,
        option_id: str,
        amount: float,
        bet_type: Optional[str] = None,
        bet_number: Optional[int] = None
    ) -> Bet:
        """Place a bet in a room.
        
        Args:
            room_id: The room ID
            player_id: The player placing the bet
            option_id: The option being bet on
            amount: The bet amount
            bet_type: Optional bet type (for roulette)
            bet_number: Optional bet number (for roulette single bets)
            
        Returns:
            The placed Bet object
            
        Raises:
            InvalidBetException: If the bet is invalid
            RoomNotFoundException: If room not found
        """
        room = self._room_service.get_room(room_id)
        if not room:
            raise RoomNotFoundException(f"Room {room_id} not found")
        
        if room.status != GameStatus.OPEN:
            raise InvalidBetException("Betting is not open")
        
        player = room.players.get(player_id)
        if not player:
            raise InvalidBetException("Player not found")
        
        if player.balance < amount:
            raise InvalidBetException("Insufficient balance")
        
        if amount <= 0:
            raise InvalidBetException("Invalid bet amount")
        
        # Check if player already bet on this option
        existing = next(
            (b for b in room.bets if b.player_id == player_id and b.option_id == option_id),
            None
        )
        if existing:
            raise InvalidBetException("Already placed a bet on this option")
        
        # Validate option exists
        option = next((o for o in room.bet_options if o.id == option_id), None)
        if not option:
            raise InvalidBetException("Invalid option")
        
        # Deduct balance and create bet
        player.balance -= amount
        
        from core.models import RouletteBetType
        bet = Bet(
            player_id=player_id,
            player_name=player.name,
            option_id=option_id,
            option_label=option.label,
            amount=amount,
            potential_win=round(amount * option.odds, 2),
            bet_type=RouletteBetType(bet_type) if bet_type else None,
            bet_number=bet_number
        )
        
        room.bets.append(bet)
        self._room_service._repo.save(room)
        
        return bet

    def process_payouts(self, room: GameRoom, winning_value: Any) -> list[dict]:
        """Process payouts for winning bets.
        
        Args:
            room: The game room
            winning_value: The winning value (option_id or number)
            
        Returns:
            List of winning bet records with payouts
        """
        game_mode = get_game_mode(room.game_mode.value)
        winning_bets = []
        
        for bet in room.bets:
            if game_mode.check_win(bet, winning_value):
                payout_multiplier = game_mode.get_payout_multiplier(bet)
                payout = bet.amount * (payout_multiplier + 1)
                
                player = room.players.get(bet.player_id)
                if player:
                    player.balance += payout
                    winning_bets.append({
                        "player_id": bet.player_id,
                        "player_name": bet.player_name,
                        "bet_amount": bet.amount,
                        "payout": payout,
                        "bet_type": bet.bet_type.value if bet.bet_type else "single"
                    })
        
        self._room_service._repo.save(room)
        return winning_bets

    def get_player_bets(self, room: GameRoom, player_id: str) -> list[Bet]:
        """Get all bets placed by a player."""
        return [b for b in room.bets if b.player_id == player_id]

    def get_total_bet_amount(self, room: GameRoom) -> float:
        """Get total amount bet in the room."""
        return sum(b.amount for b in room.bets)

    def get_bets_on_option(self, room: GameRoom, option_id: str) -> list[Bet]:
        """Get all bets on a specific option."""
        return [b for b in room.bets if b.option_id == option_id]
