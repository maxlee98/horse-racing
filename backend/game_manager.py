import uuid
import random
import asyncio
from typing import Optional
from models import GameRoom, Player, Bet, BetOption, GameStatus, GameMode


class GameManager:
    def __init__(self):
        self.rooms: dict[str, GameRoom] = {}

    def create_room(self, host_id: str, title: str, description: str, bet_options: list[dict], 
                    game_mode: GameMode = GameMode.STANDARD, use_randomized_probabilities: bool = False) -> GameRoom:
        room_id = str(uuid.uuid4())[:8].upper()
        options = [BetOption(**opt) for opt in bet_options] if bet_options else []
        
        # Calculate probabilities based on inverse of odds (lower odds = higher probability)
        if options:
            # Inverse odds: 1/odds gives weight, normalize to get probability
            inverse_odds = [1.0 / opt.odds for opt in options]
            total_inverse = sum(inverse_odds)
            for i, opt in enumerate(options):
                opt.probability = round(inverse_odds[i] / total_inverse, 4)
        
        room = GameRoom(
            room_id=room_id,
            host_id=host_id,
            title=title,
            description=description,
            bet_options=options,
            game_mode=game_mode,
            use_randomized_probabilities=use_randomized_probabilities,
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
            "game_mode": room.game_mode.value,
            "round_number": room.round_number,
            "use_randomized_probabilities": room.use_randomized_probabilities,
        }

    def update_probabilities(self, room_id: str, probabilities: dict[str, float], host_id: str) -> tuple[bool, str]:
        """Update win probabilities for bet options and recalculate odds."""
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found"
        if room.host_id != host_id:
            return False, "Not authorized"
        
        for option in room.bet_options:
            if option.id in probabilities:
                option.probability = max(0.01, min(1.0, probabilities[option.id]))  # Min 1% prob
        
        # Recalculate odds based on probabilities (lower prob = higher odds)
        self._update_odds_from_probabilities(room)
        
        return True, "Probabilities and odds updated"

    def _update_odds_from_probabilities(self, room: GameRoom):
        """Update odds based on probabilities. Lower probability = higher odds."""
        # Calculate average probability
        total_prob = sum(opt.probability for opt in room.bet_options)
        if total_prob == 0:
            return
        
        # Calculate odds: inverse of probability, normalized to be competitive
        # Base odds = 1 / probability, then scaled
        for opt in room.bet_options:
            if opt.probability > 0:
                # Odds formula: 0.9 / probability gives reasonable odds
                # e.g., 50% prob = 1.8x, 25% prob = 3.6x, 10% prob = 9x
                opt.odds = round(0.9 / opt.probability, 2)
            else:
                opt.odds = 99.0  # Very high odds for near-impossible outcomes

    def randomize_probabilities(self, room_id: str, host_id: str) -> tuple[bool, str]:
        """Randomize probabilities for a new round while keeping them somewhat balanced."""
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found"
        if room.host_id != host_id:
            return False, "Not authorized"
        
        n = len(room.bet_options)
        if n == 0:
            return False, "No bet options"
        
        # Generate random probabilities and normalize to sum to 1
        raw_probs = [random.random() for _ in range(n)]
        total = sum(raw_probs)
        normalized_probs = [p / total for p in raw_probs]
        
        for i, option in enumerate(room.bet_options):
            option.probability = round(normalized_probs[i], 4)
        
        # Update odds based on new probabilities
        self._update_odds_from_probabilities(room)
        
        return True, "Probabilities and odds randomized"

    def next_round(self, room_id: str, host_id: str) -> tuple[bool, str]:
        """Move to next round: clear bets and winner, randomize probabilities, increment round number."""
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found"
        if room.host_id != host_id:
            return False, "Not authorized"
        
        # Clear bets and winner
        room.bets = []
        room.winner_option_id = None
        room.status = GameStatus.WAITING
        room.round_number += 1
        
        # Randomize probabilities for the new round
        self.randomize_probabilities(room_id, host_id)
        
        return True, "Next round started"

    def reset_lobby(self, room_id: str, host_id: str) -> tuple[bool, str]:
        """Reset the entire lobby - clears everything including player balances."""
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found"
        if room.host_id != host_id:
            return False, "Not authorized"
        
        room.status = GameStatus.WAITING
        room.bets = []
        room.winner_option_id = None
        room.round_number = 1
        
        # Reset all player balances
        for player in room.players.values():
            player.balance = 1000.0
        
        # Reset to equal probabilities
        if room.bet_options:
            prob = 1.0 / len(room.bet_options)
            for opt in room.bet_options:
                opt.probability = prob
        
        return True, "Lobby reset"

    def select_winner_by_probability(self, room_id: str, host_id: str) -> tuple[bool, str, Optional[str]]:
        """Select winner based on configured probabilities."""
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found", None
        if room.host_id != host_id:
            return False, "Not authorized", None
        
        if not room.bet_options:
            return False, "No bet options", None
        
        # Weighted random selection based on probabilities
        options = room.bet_options
        probs = [opt.probability for opt in options]
        total_prob = sum(probs)
        
        if total_prob == 0:
            # Equal probability if all are 0
            winner = random.choice(options)
        else:
            # Normalize and select
            normalized = [p / total_prob for p in probs]
            r = random.random()
            cumulative = 0
            winner = options[0]
            for i, prob in enumerate(normalized):
                cumulative += prob
                if r <= cumulative:
                    winner = options[i]
                    break
        
        # Set the winner
        success, msg = self.set_winner(room_id, winner.id, host_id)
        return success, msg, winner.id if success else None

    async def run_horse_race(self, room_id: str, host_id: str, broadcast_callback) -> tuple[bool, str, Optional[str]]:
        """Run a horse race animation and determine winner by probability."""
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found", None
        if room.host_id != host_id:
            return False, "Not authorized", None
        
        if not room.bet_options:
            return False, "No horses in race", None
        
        import time
        start_time = time.time()
        
        # Notify race started
        await broadcast_callback({
            "type": "race_started",
            "data": {"horses": [opt.model_dump() for opt in room.bet_options], "start_time": start_time}
        })
        
        # Track cumulative position and finish times for each horse
        horse_positions: dict[str, float] = {opt.id: 0.0 for opt in room.bet_options}
        horse_finish_times: dict[str, float] = {}  # horse_id -> finish time
        horse_ranks: dict[str, int] = {}  # horse_id -> rank
        current_rank = 1
        
        # Race simulation - each horse progresses at different speeds
        max_race_time = 15.0  # Maximum race duration in seconds
        elapsed = 0.0
        step_duration = 0.05  # 50ms per update
        
        while elapsed < max_race_time and len(horse_finish_times) < len(room.bet_options):
            await asyncio.sleep(step_duration)
            elapsed += step_duration
            
            # Update each horse's position
            for opt in room.bet_options:
                if opt.id in horse_finish_times:
                    continue  # Already finished
                
                # Speed based on probability - higher prob = faster
                base_speed = 100 / (8 + (1 - opt.probability) * 7)  # 8-15 seconds to finish
                speed_variation = random.uniform(0.8, 1.2)
                speed = base_speed * speed_variation
                
                # Update position
                new_position = horse_positions[opt.id] + speed * step_duration
                
                # Check if finished
                if new_position >= 100.0:
                    new_position = 100.0
                    horse_finish_times[opt.id] = elapsed
                    horse_ranks[opt.id] = current_rank
                    current_rank += 1
                
                horse_positions[opt.id] = new_position
            
            # Create positions array with current rankings
            positions = []
            for opt in room.bet_options:
                positions.append({
                    "option_id": opt.id,
                    "label": opt.label,
                    "position": round(horse_positions[opt.id], 1),
                    "probability": opt.probability,
                    "rank": horse_ranks.get(opt.id, 0),
                    "finish_time": round(horse_finish_times.get(opt.id, 0), 2) if opt.id in horse_finish_times else None
                })
            
            progress = len(horse_finish_times) / len(room.bet_options)
            
            await broadcast_callback({
                "type": "race_progress",
                "data": {
                    "positions": positions, 
                    "progress": progress,
                    "elapsed_time": round(elapsed, 2),
                    "finished_count": len(horse_finish_times)
                }
            })
        
        # Determine winner based on race finish (1st place finisher is the winner)
        # Sort by finish time and get the first one
        sorted_by_time = sorted(
            [(opt_id, time) for opt_id, time in horse_finish_times.items()],
            key=lambda x: x[1]
        )
        winner_id = sorted_by_time[0][0] if sorted_by_time else room.bet_options[0].id
        
        # Set the winner
        success, msg = self.set_winner(room_id, winner_id, host_id)
        
        if success and winner_id:
            winner = next((o for o in room.bet_options if o.id == winner_id), None)
            
            # Create final results with all horses at 100% and rankings
            final_positions = []
            for opt in room.bet_options:
                is_winner = opt.id == winner_id
                # Ensure all finished horses have a rank
                if opt.id not in horse_ranks:
                    horse_ranks[opt.id] = current_rank
                    current_rank += 1
                if opt.id not in horse_finish_times:
                    horse_finish_times[opt.id] = elapsed
                
                final_positions.append({
                    "option_id": opt.id,
                    "label": opt.label,
                    "position": 100.0,
                    "probability": opt.probability,
                    "rank": horse_ranks[opt.id],
                    "finish_time": round(horse_finish_times[opt.id], 2),
                    "is_winner": is_winner
                })
            
            # Sort by rank for the results
            final_positions.sort(key=lambda x: x["rank"])
            
            # Show final results
            await broadcast_callback({
                "type": "race_progress",
                "data": {
                    "positions": final_positions, 
                    "progress": 1.0,
                    "race_complete": True,
                    "message": "🏁 Race Complete!",
                    "winner_id": winner_id
                }
            })
            
            await asyncio.sleep(2)
            
            # Countdown before revealing winner
            for count in [3, 2, 1]:
                await broadcast_callback({
                    "type": "race_progress",
                    "data": {
                        "positions": final_positions, 
                        "progress": 1.0,
                        "race_complete": True,
                        "countdown": count,
                        "message": f"Winner revealed in {count}...",
                        "winner_id": winner_id
                    }
                })
                await asyncio.sleep(1)
            
            await broadcast_callback({
                "type": "race_ended",
                "data": {
                    "winner_id": winner_id,
                    "winner_label": winner.label if winner else "Unknown",
                    "final_results": final_positions,
                    "race_duration": round(elapsed, 2),
                    "room_state": self.get_room_state(room_id)
                }
            })
        
        return success, msg, winner_id
