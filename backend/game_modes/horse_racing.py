"""Horse Racing game mode implementation."""

import random
import asyncio
from typing import Optional, Callable, Any
from core.models import GameRoom, Bet, GameStatus, BetOption
from .base import GameModeStrategy


class HorseRacingMode(GameModeStrategy):
    """Horse racing with animated race."""

    @property
    def name(self) -> str:
        return "horse_racing"

    def initialize_default_options(self, room: GameRoom) -> None:
        """Set up horse racing options with named horses."""
        horses = [
            ("Thunder Bolt", 2.5),
            ("Midnight Runner", 3.0),
            ("Golden Mane", 2.0),
            ("Silver Streak", 4.0),
            ("Wild Spirit", 3.5),
        ]
        n = len(horses)
        room.bet_options = [
            BetOption(
                id=f"horse_{i}",
                label=name,
                odds=odds,
                probability=round(1.0 / n, 4)
            )
            for i, (name, odds) in enumerate(horses)
        ]

    def calculate_probabilities(self, room: GameRoom) -> None:
        """Calculate probabilities based on inverse odds."""
        if not room.bet_options:
            return
        
        inverse_odds = [1.0 / opt.odds for opt in room.bet_options]
        total_inverse = sum(inverse_odds)
        
        for i, opt in enumerate(room.bet_options):
            opt.probability = round(inverse_odds[i] / total_inverse, 4)

    async def run_animation(
        self,
        room: GameRoom,
        broadcast: Callable[[dict], Any]
    ) -> tuple[bool, str, Optional[str]]:
        """Run horse race animation with momentum-based speed changes."""
        import time
        start_time = time.time()
        
        # Notify race started
        await broadcast({
            "type": "race_started",
            "data": {
                "horses": [opt.model_dump() for opt in room.bet_options],
                "start_time": start_time
            }
        })
        
        # Track positions and finish times
        horse_positions: dict[str, float] = {opt.id: 0.0 for opt in room.bet_options}
        horse_finish_times: dict[str, float] = {}
        horse_ranks: dict[str, int] = {}
        current_rank = 1
        
        # Momentum tracking - horses behind gain speed, horses ahead lose speed
        horse_momentum: dict[str, float] = {opt.id: 0.0 for opt in room.bet_options}
        
        # Momentum mechanics constants
        max_momentum_boost = 0.30   # max 30% speed boost when behind
        max_momentum_penalty = 0.20  # max 20% speed penalty when ahead
        momentum_decay = 0.05         # base momentum changes per tick
        momentum_random_factor = 0.03 # random noise added to momentum changes
        surge_chance = 0.05          # 5% chance per horse per tick for random surge
        surge_strength = 0.15        # strength of random momentum surge
        
        # Race parameters
        max_race_time = 15.0
        elapsed = 0.0
        step_duration = 0.05
        
        while elapsed < max_race_time and len(horse_finish_times) < len(room.bet_options):
            await asyncio.sleep(step_duration)
            elapsed += step_duration
            
            # Calculate average position of all racing horses
            racing_positions = [
                horse_positions[opt.id] 
                for opt in room.bet_options 
                if opt.id not in horse_finish_times
            ]
            avg_position = sum(racing_positions) / len(racing_positions) if racing_positions else 50.0
            
            # Update each horse
            for opt in room.bet_options:
                if opt.id in horse_finish_times:
                    continue
                
                current_pos = horse_positions[opt.id]
                
                # Calculate momentum based on relative position
                if current_pos < avg_position:
                    # Behind: gain positive momentum (speeding up)
                    base_change = momentum_decay * (avg_position - current_pos) / 50
                    # Random element - can be 0.5x to 1.5x the base
                    random_multiplier = random.uniform(0.5, 1.5)
                    momentum_change = base_change * random_multiplier
                    
                    horse_momentum[opt.id] = min(
                        horse_momentum[opt.id] + momentum_change, 
                        max_momentum_boost
                    )
                else:
                    # Ahead: lose momentum (slowing down)
                    base_change = momentum_decay * (current_pos - avg_position) / 50
                    random_multiplier = random.uniform(0.5, 1.5)
                    momentum_change = base_change * random_multiplier
                    
                    horse_momentum[opt.id] = max(
                        horse_momentum[opt.id] - momentum_change, 
                        -max_momentum_penalty
                    )
                
                # Random momentum surge - any horse can burst forward or slow down
                if random.random() < surge_chance:
                    surge_direction = random.choice([1, -1])
                    surge_amount = random.uniform(surge_strength * 0.5, surge_strength)
                    horse_momentum[opt.id] += surge_direction * surge_amount
                    # Clamp to bounds
                    horse_momentum[opt.id] = max(
                        -max_momentum_penalty, 
                        min(max_momentum_boost, horse_momentum[opt.id])
                    )
                
                # Apply momentum to speed
                base_speed = 100 / (8 + (1 - opt.probability) * 7)
                speed_variation = random.uniform(0.8, 1.2)
                momentum_multiplier = 1.0 + horse_momentum[opt.id]
                speed = base_speed * speed_variation * momentum_multiplier
                
                new_position = current_pos + speed * step_duration
                
                if new_position >= 100.0:
                    new_position = 100.0
                    horse_finish_times[opt.id] = elapsed
                    horse_ranks[opt.id] = current_rank
                    current_rank += 1
                
                horse_positions[opt.id] = new_position
            
            # Send progress update with momentum data
            positions = []
            dramatic_event = None
            for opt in room.bet_options:
                current_pos = horse_positions[opt.id]
                momentum = horse_momentum[opt.id]
                momentum_surge = momentum > 0.2
                
                positions.append({
                    "option_id": opt.id,
                    "label": opt.label,
                    "position": round(current_pos, 1),
                    "probability": opt.probability,
                    "rank": horse_ranks.get(opt.id, 0),
                    "finish_time": round(horse_finish_times.get(opt.id, 0), 2) if opt.id in horse_finish_times else None,
                    "momentum": round(momentum, 3),
                    "momentum_surge": momentum_surge,
                })
                
                # Detect dramatic events
                if momentum > 0.15 and current_pos < avg_position - 10:
                    dramatic_event = f"🔥 {opt.label} is making a comeback!"
                elif momentum < -0.10 and current_pos > avg_position + 10:
                    dramatic_event = f"💨 {opt.label} is fading!"
                elif abs(momentum) > 0.25:
                    dramatic_event = f"⚡ {opt.label} gets a sudden burst!"
            
            progress = len(horse_finish_times) / len(room.bet_options)
            
            await broadcast({
                "type": "race_progress",
                "data": {
                    "positions": positions,
                    "progress": progress,
                    "elapsed_time": round(elapsed, 2),
                    "finished_count": len(horse_finish_times),
                    "dramatic_event": dramatic_event,
                }
            })
        
        # Determine winner
        sorted_by_time = sorted(
            [(opt_id, t) for opt_id, t in horse_finish_times.items()],
            key=lambda x: x[1]
        )
        winner_id = sorted_by_time[0][0] if sorted_by_time else room.bet_options[0].id
        
        # Set winner
        room.status = GameStatus.ENDED
        room.winner_option_id = winner_id
        
        # Create final results
        final_positions = []
        for opt in room.bet_options:
            is_winner = opt.id == winner_id
            
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
        
        final_positions.sort(key=lambda x: x["rank"])
        winner = next((opt for opt in room.bet_options if opt.id == winner_id), None)
        
        # Show race complete and send final results immediately
        await broadcast({
            "type": "race_progress",
            "data": {
                "positions": final_positions,
                "progress": 1.0,
                "race_complete": True,
                "message": "🏁 Race Complete!",
                "winner_id": winner_id
            }
        })
        
        # Return winning_bets info along with the result
        # The main.py will add winning_bets and broadcast again
        return True, f"Race complete! Winner: {winner.label if winner else 'Unknown'}", winner_id

    def check_win(self, bet: Bet, winning_value: Any) -> bool:
        """Check if bet wins - compare option_id."""
        return bet.option_id == winning_value

    def get_payout_multiplier(self, bet: Bet) -> int:
        """Get payout multiplier."""
        return 1  # Uses bet.potential_win

    @staticmethod
    def get_preset_options() -> list[dict]:
        """Get the standard horse racing betting options."""
        return [
            {"id": "1", "label": "🐎 Thunder Bolt", "odds": 2.5},
            {"id": "2", "label": "🐎 Midnight Runner", "odds": 3.0},
            {"id": "3", "label": "🐎 Golden Mane", "odds": 2.0},
            {"id": "4", "label": "🐎 Silver Streak", "odds": 4.0},
            {"id": "5", "label": "🐎 Wild Spirit", "odds": 3.5},
        ]
