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
        """Run horse race animation."""
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
        
        # Race parameters
        max_race_time = 15.0
        elapsed = 0.0
        step_duration = 0.05
        
        while elapsed < max_race_time and len(horse_finish_times) < len(room.bet_options):
            await asyncio.sleep(step_duration)
            elapsed += step_duration
            
            # Update each horse
            for opt in room.bet_options:
                if opt.id in horse_finish_times:
                    continue
                
                # Speed based on probability
                base_speed = 100 / (8 + (1 - opt.probability) * 7)
                speed_variation = random.uniform(0.8, 1.2)
                speed = base_speed * speed_variation
                
                new_position = horse_positions[opt.id] + speed * step_duration
                
                if new_position >= 100.0:
                    new_position = 100.0
                    horse_finish_times[opt.id] = elapsed
                    horse_ranks[opt.id] = current_rank
                    current_rank += 1
                
                horse_positions[opt.id] = new_position
            
            # Send progress update
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
            
            await broadcast({
                "type": "race_progress",
                "data": {
                    "positions": positions,
                    "progress": progress,
                    "elapsed_time": round(elapsed, 2),
                    "finished_count": len(horse_finish_times)
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
        
        # Send final results
        await broadcast({
            "type": "race_ended",
            "data": {
                "winner_id": winner_id,
                "winner_label": winner.label if winner else "Unknown",
                "final_results": final_positions,
                "race_duration": round(elapsed, 2),
            }
        })
        
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
