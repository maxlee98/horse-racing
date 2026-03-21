import uuid
import random
import asyncio
import math
from typing import Optional
from models import GameRoom, Player, Bet, BetOption, GameStatus, GameMode, RouletteBetType

# American Roulette wheel order (clockwise from 0)
AMERICAN_ROULETTE_ORDER = [
    0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1,
    37,  # 00 represented as 37 for calculations
    27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16, 4, 23, 35, 14, 2
]

# Number colors (0 and 00 are green)
ROULETTE_COLORS = {
    0: "green",
    37: "green",  # 00
    1: "red", 3: "red", 5: "red", 7: "red", 9: "red",
    12: "red", 14: "red", 16: "red", 18: "red",
    19: "red", 21: "red", 23: "red", 25: "red", 27: "red",
    30: "red", 32: "red", 34: "red", 36: "red",
    2: "black", 4: "black", 6: "black", 8: "black", 10: "black",
    11: "black", 13: "black", 15: "black", 17: "black",
    20: "black", 22: "black", 24: "black", 26: "black", 28: "black",
    29: "black", 31: "black", 33: "black", 35: "black"
}

# Payouts for each bet type
ROULETTE_PAYOUTS = {
    RouletteBetType.SINGLE: 35,
    RouletteBetType.RED: 1,
    RouletteBetType.BLACK: 1,
    RouletteBetType.EVEN: 1,
    RouletteBetType.ODD: 1,
    RouletteBetType.LOW: 1,
    RouletteBetType.HIGH: 1,
    RouletteBetType.FIRST_DOZEN: 2,
    RouletteBetType.SECOND_DOZEN: 2,
    RouletteBetType.THIRD_DOZEN: 2,
    RouletteBetType.FIRST_COLUMN: 2,
    RouletteBetType.SECOND_COLUMN: 2,
    RouletteBetType.THIRD_COLUMN: 2,
}


class GameManager:
    def __init__(self):
        self.rooms: dict[str, GameRoom] = {}

    def create_room(self, host_id: str, title: str, description: str, bet_options: list[dict], 
                    game_mode: GameMode = GameMode.STANDARD, use_randomized_probabilities: bool = False) -> GameRoom:
        room_id = str(uuid.uuid4())[:8].upper()
        options = [BetOption(**opt) for opt in bet_options] if bet_options else []
        
        if game_mode == GameMode.ROULETTE:
            # For roulette, all numbers have equal probability (1/38)
            # Other bet types (red/black/dozens etc.) derive their probability from this
            for opt in options:
                if opt.label.isdigit() or opt.label == '00':
                    # Single numbers: 1/38 chance
                    opt.probability = round(1.0 / 38, 4)
                elif opt.label.lower() in ['red', 'black']:
                    # 18/38 chance
                    opt.probability = round(18.0 / 38, 4)
                elif opt.label.lower() in ['even', 'odd']:
                    # 18/38 chance (excluding 0 and 00)
                    opt.probability = round(18.0 / 38, 4)
                elif opt.label in ['1-18 (Low)', '19-36 (High)']:
                    # 18/38 chance
                    opt.probability = round(18.0 / 38, 4)
                elif '12' in opt.label:
                    # Dozens: 12/38 chance
                    opt.probability = round(12.0 / 38, 4)
                elif 'Column' in opt.label:
                    # Columns: 12/38 chance
                    opt.probability = round(12.0 / 38, 4)
                else:
                    opt.probability = round(1.0 / 38, 4)
        elif options:
            # Calculate probabilities based on inverse of odds (lower odds = higher probability)
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

    def check_roulette_win(self, bet: Bet, winning_number: int) -> bool:
        """Check if a roulette bet wins based on the winning number."""
        bet_type = bet.bet_type
        bet_number = bet.bet_number
        
        if not bet_type:
            # Default to checking by option_id for backwards compatibility
            return bet.option_id == str(winning_number)
        
        if bet_type == RouletteBetType.SINGLE:
            return bet_number == winning_number
        
        color = ROULETTE_COLORS.get(winning_number, "green")
        
        if bet_type == RouletteBetType.RED:
            return color == "red"
        elif bet_type == RouletteBetType.BLACK:
            return color == "black"
        elif bet_type == RouletteBetType.EVEN:
            return winning_number != 0 and winning_number != 37 and winning_number % 2 == 0
        elif bet_type == RouletteBetType.ODD:
            return winning_number != 0 and winning_number != 37 and winning_number % 2 == 1
        elif bet_type == RouletteBetType.LOW:
            return 1 <= winning_number <= 18
        elif bet_type == RouletteBetType.HIGH:
            return 19 <= winning_number <= 36
        elif bet_type == RouletteBetType.FIRST_DOZEN:
            return 1 <= winning_number <= 12
        elif bet_type == RouletteBetType.SECOND_DOZEN:
            return 13 <= winning_number <= 24
        elif bet_type == RouletteBetType.THIRD_DOZEN:
            return 25 <= winning_number <= 36
        elif bet_type == RouletteBetType.FIRST_COLUMN:
            return winning_number != 0 and winning_number != 37 and winning_number % 3 == 1
        elif bet_type == RouletteBetType.SECOND_COLUMN:
            return winning_number != 0 and winning_number != 37 and winning_number % 3 == 2
        elif bet_type == RouletteBetType.THIRD_COLUMN:
            return winning_number != 0 and winning_number != 37 and winning_number % 3 == 0
        
        return False

    async def run_roulette_spin(self, room_id: str, host_id: str, broadcast_callback) -> tuple[bool, str, Optional[int]]:
        """Run a roulette wheel spin animation and determine the winning number."""
        room = self.get_room(room_id)
        if not room:
            return False, "Room not found", None
        if room.host_id != host_id:
            return False, "Not authorized", None
        
        # Select winning number (random 0-37, where 37 represents 00)
        winning_number = random.choice(AMERICAN_ROULETTE_ORDER)
        winning_color = ROULETTE_COLORS.get(winning_number, "green")
        winning_index = AMERICAN_ROULETTE_ORDER.index(winning_number)
        
        # Calculate final wheel position (each pocket is 360/38 = 9.47 degrees)
        pocket_angle = 360 / 38
        # Add some randomness within the pocket for realistic ball position
        ball_offset = random.uniform(-pocket_angle/3, pocket_angle/3)
        target_wheel_rotation = 360 - (winning_index * pocket_angle) + ball_offset
        
        # Notify roulette started
        await broadcast_callback({
            "type": "roulette_started",
            "data": {
                "wheel_numbers": AMERICAN_ROULETTE_ORDER,
                "colors": ROULETTE_COLORS,
                "duration": 10.0
            }
        })
        
        # Animation phases
        phase_duration = {
            "accelerating": 0.5,
            "spinning": 2.0,
            "decelerating": 3.5,
            "settling": 1.0
        }
        
        wheel_rotation = 0.0
        ball_position = 0.0  # Angle in degrees
        ball_radius = 100.0  # Distance from center (starts at outer track)
        
        # Phase 1: Accelerating
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < phase_duration["accelerating"]:
            elapsed = asyncio.get_event_loop().time() - start_time
            progress = elapsed / phase_duration["accelerating"]
            
            # Accelerate wheel and ball
            wheel_rotation = progress * 720  # 2 rotations during acceleration
            ball_position = -progress * 1080  # 3 rotations opposite direction
            
            await broadcast_callback({
                "type": "roulette_progress",
                "data": {
                    "phase": "accelerating",
                    "wheel_rotation": round(wheel_rotation, 2),
                    "ball_position": round(ball_position, 2),
                    "ball_radius": round(ball_radius, 2),
                    "progress": progress * 0.1
                }
            })
            await asyncio.sleep(0.05)
        
        # Phase 2: Constant speed spinning
        wheel_velocity = 720 / phase_duration["accelerating"]  # degrees per second
        ball_velocity = -1080 / phase_duration["accelerating"]
        
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < phase_duration["spinning"]:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            wheel_rotation += wheel_velocity * 0.05
            ball_position += ball_velocity * 0.05
            
            await broadcast_callback({
                "type": "roulette_progress",
                "data": {
                    "phase": "spinning",
                    "wheel_rotation": round(wheel_rotation % 360, 2),
                    "ball_position": round(ball_position % 360, 2),
                    "ball_radius": round(ball_radius, 2),
                    "progress": 0.1 + (elapsed / phase_duration["spinning"]) * 0.3
                }
            })
            await asyncio.sleep(0.05)
        
        # Phase 3: Decelerating + ball dropping
        start_time = asyncio.get_event_loop().time()
        deceleration_duration = phase_duration["decelerating"]
        
        # Calculate how many more rotations to reach target
        current_wheel_pos = wheel_rotation % 360
        rotations_needed = 3  # At least 3 more rotations
        total_rotation_needed = rotations_needed * 360 + (target_wheel_rotation - current_wheel_pos) % 360
        
        # Deceleration curve (ease out)
        while asyncio.get_event_loop().time() - start_time < deceleration_duration:
            elapsed = asyncio.get_event_loop().time() - start_time
            t = elapsed / deceleration_duration
            
            # Ease out cubic
            ease = 1 - pow(1 - t, 3)
            
            wheel_rotation = current_wheel_pos + total_rotation_needed * ease
            
            # Ball slows faster and drops inward
            ball_velocity *= 0.985  # Friction
            ball_position += ball_velocity * 0.05
            
            # Ball drops inward as it slows
            ball_radius = 100 - (ease * 40) + random.uniform(-2, 2)  # Bounces slightly
            
            await broadcast_callback({
                "type": "roulette_progress",
                "data": {
                    "phase": "decelerating",
                    "wheel_rotation": round(wheel_rotation % 360, 2),
                    "ball_position": round(ball_position % 360, 2),
                    "ball_radius": round(max(45, ball_radius), 2),
                    "progress": 0.4 + t * 0.4
                }
            })
            await asyncio.sleep(0.05)
        
        # Phase 4: Ball settling into pocket
        start_time = asyncio.get_event_loop().time()
        final_wheel_pos = target_wheel_rotation % 360
        
        while asyncio.get_event_loop().time() - start_time < phase_duration["settling"]:
            elapsed = asyncio.get_event_loop().time() - start_time
            t = elapsed / phase_duration["settling"]
            
            # Small bounces as ball settles
            bounce = math.sin(t * math.pi * 4) * (1 - t) * 3
            
            wheel_rotation = final_wheel_pos + bounce
            ball_position = (winning_index * pocket_angle) + ball_offset + bounce
            ball_radius = 60  # In the pocket
            
            await broadcast_callback({
                "type": "roulette_ball_settling",
                "data": {
                    "phase": "settling",
                    "wheel_rotation": round(wheel_rotation, 2),
                    "ball_position": round(ball_position, 2),
                    "ball_radius": round(ball_radius, 2),
                    "progress": 0.8 + t * 0.15
                }
            })
            await asyncio.sleep(0.05)
        
        # Countdown before revealing
        for count in [3, 2, 1]:
            await broadcast_callback({
                "type": "roulette_progress",
                "data": {
                    "phase": "revealing",
                    "countdown": count,
                    "wheel_rotation": round(final_wheel_pos, 2),
                    "ball_position": round(winning_index * pocket_angle + ball_offset, 2),
                    "ball_radius": 60,
                    "progress": 0.95 + (4 - count) * 0.017,
                    "message": f"Revealing in {count}..."
                }
            })
            await asyncio.sleep(1)
        
        # Set the winner and calculate payouts
        room.status = GameStatus.ENDED
        
        # Find or create the winning option
        winning_option_id = None
        for opt in room.bet_options:
            if opt.label == str(winning_number) or opt.id == str(winning_number):
                winning_option_id = opt.id
                room.winner_option_id = opt.id
                break
        
        # If no matching option found, use first option as winner (fallback)
        if not winning_option_id and room.bet_options:
            winning_option_id = room.bet_options[0].id
            room.winner_option_id = winning_option_id
        
        # Pay out winners based on roulette rules
        total_payout = 0
        winning_bets = []
        
        for bet in room.bets:
            if self.check_roulette_win(bet, winning_number):
                # Calculate payout based on bet type
                bet_type = bet.bet_type or RouletteBetType.SINGLE
                payout_multiplier = ROULETTE_PAYOUTS.get(bet_type, 35)
                payout = bet.amount * (payout_multiplier + 1)  # Return bet + winnings
                
                player = room.players.get(bet.player_id)
                if player:
                    player.balance += payout
                    total_payout += payout
                    winning_bets.append({
                        "player_id": bet.player_id,
                        "player_name": bet.player_name,
                        "bet_amount": bet.amount,
                        "payout": payout,
                        "bet_type": bet_type.value,
                        "option_id": bet.option_id, 
                    })
        
        # Display name for winning number
        display_number = "00" if winning_number == 37 else str(winning_number)
        
        await broadcast_callback({
            "type": "roulette_ended",
            "data": {
                "winning_number": display_number,
                "winning_number_int": winning_number,
                "winning_color": winning_color,
                "winning_option_id": winning_option_id,
                "wheel_rotation": round(final_wheel_pos, 2),
                "ball_position": round(winning_index * pocket_angle + ball_offset, 2),
                "total_payout": round(total_payout, 2),
                "winning_bets": winning_bets,
                "room_state": self.get_room_state(room_id)
            }
        })
        
        return True, f"Roulette spin complete! Winning number: {display_number} ({winning_color})", winning_number
