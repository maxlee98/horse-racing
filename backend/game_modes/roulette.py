"""Roulette game mode implementation."""

import random
import asyncio
import math
from typing import Optional, Callable, Any
from core.models import (
    GameRoom, Bet, GameStatus, 
    RouletteBetType, BetOption
)
from core.constants import GameConstants
from .base import GameModeStrategy


# Import constants from centralized location
AMERICAN_ROULETTE_ORDER = GameConstants.ROULETTE_WHEEL_ORDER
ROULETTE_COLORS = GameConstants.ROULETTE_COLORS
ROULETTE_PAYOUTS = {
    RouletteBetType.SINGLE: GameConstants.ROULETTE_PAYOUTS["single"],
    RouletteBetType.RED: GameConstants.ROULETTE_PAYOUTS["red"],
    RouletteBetType.BLACK: GameConstants.ROULETTE_PAYOUTS["black"],
    RouletteBetType.EVEN: GameConstants.ROULETTE_PAYOUTS["even"],
    RouletteBetType.ODD: GameConstants.ROULETTE_PAYOUTS["odd"],
    RouletteBetType.LOW: GameConstants.ROULETTE_PAYOUTS["low"],
    RouletteBetType.HIGH: GameConstants.ROULETTE_PAYOUTS["high"],
    RouletteBetType.FIRST_DOZEN: GameConstants.ROULETTE_PAYOUTS["first_dozen"],
    RouletteBetType.SECOND_DOZEN: GameConstants.ROULETTE_PAYOUTS["second_dozen"],
    RouletteBetType.THIRD_DOZEN: GameConstants.ROULETTE_PAYOUTS["third_dozen"],
    RouletteBetType.FIRST_COLUMN: GameConstants.ROULETTE_PAYOUTS["first_column"],
    RouletteBetType.SECOND_COLUMN: GameConstants.ROULETTE_PAYOUTS["second_column"],
    RouletteBetType.THIRD_COLUMN: GameConstants.ROULETTE_PAYOUTS["third_column"],
}


class RouletteMode(GameModeStrategy):
    """American Roulette with spinning wheel animation."""

    @property
    def name(self) -> str:
        return "roulette"

    def calculate_probabilities(self, room: GameRoom) -> None:
        """Calculate roulette-specific probabilities."""
        for opt in room.bet_options:
            if opt.label.isdigit() or opt.label == '00':
                # Single numbers: 1/38 chance
                opt.probability = round(1.0 / 38, 4)
            elif opt.label.lower() in ['red', 'black']:
                # 18/38 chance
                opt.probability = round(18.0 / 38, 4)
            elif opt.label.lower() in ['even', 'odd']:
                # 18/38 chance (excluding 0 and 00)
                opt.probability = round(18.0 / 38, 4)
            elif '18' in opt.label or 'low' in opt.label.lower() or 'high' in opt.label.lower():
                # 18/38 chance
                opt.probability = round(18.0 / 38, 4)
            elif '12' in opt.label:
                # Dozens: 12/38 chance
                opt.probability = round(12.0 / 38, 4)
            elif 'column' in opt.label.lower():
                # Columns: 12/38 chance
                opt.probability = round(12.0 / 38, 4)
            else:
                opt.probability = round(1.0 / 38, 4)

    async def run_animation(
        self,
        room: GameRoom,
        broadcast: Callable[[dict], Any]
    ) -> tuple[bool, str, Optional[Any]]:
        """Run roulette wheel spin animation."""
        # Select winning number
        winning_number = random.choice(AMERICAN_ROULETTE_ORDER)
        winning_color = ROULETTE_COLORS.get(winning_number, "green")
        winning_index = AMERICAN_ROULETTE_ORDER.index(winning_number)
        
        # Calculate final wheel position
        pocket_angle = 360 / 38
        ball_offset = random.uniform(-pocket_angle/3, pocket_angle/3)
        target_wheel_rotation = 360 - (winning_index * pocket_angle) + ball_offset
        
        # Notify roulette started
        await broadcast({
            "type": "roulette_started",
            "data": {
                "wheel_numbers": AMERICAN_ROULETTE_ORDER,
                "colors": ROULETTE_COLORS,
                "duration": 10.0
            }
        })
        
        # Run animation phases
        await self._run_acceleration_phase(broadcast)
        await self._run_spinning_phase(broadcast)
        await self._run_deceleration_phase(broadcast, target_wheel_rotation, winning_index, pocket_angle, ball_offset)
        await self._run_settling_phase(broadcast, target_wheel_rotation, winning_index, pocket_angle, ball_offset)
        
        # Countdown before revealing
        for count in [3, 2, 1]:
            await broadcast({
                "type": "roulette_progress",
                "data": {
                    "phase": "revealing",
                    "countdown": count,
                    "wheel_rotation": round(target_wheel_rotation % 360, 2),
                    "ball_position": round(winning_index * pocket_angle + ball_offset, 2),
                    "ball_radius": 60,
                    "progress": 0.95 + (4 - count) * 0.017,
                    "message": f"Revealing in {count}..."
                }
            })
            await asyncio.sleep(1)
        
        # Set winner
        room.status = GameStatus.ENDED
        winning_option_id = self._find_winning_option(room, winning_number)
        room.winner_option_id = winning_option_id
        
        display_number = "00" if winning_number == 37 else str(winning_number)
        
        # Return winning data for main.py to broadcast after processing payouts
        return True, f"Roulette spin complete! Winning number: {display_number} ({winning_color})", {
            "winning_number": display_number,
            "winning_number_int": winning_number,
            "winning_color": winning_color,
            "winning_option_id": winning_option_id,
        }

    async def _run_acceleration_phase(self, broadcast: Callable[[dict], Any]) -> None:
        """Phase 1: Wheel and ball accelerate."""
        duration = 0.5
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < duration:
            elapsed = asyncio.get_event_loop().time() - start_time
            progress = elapsed / duration
            
            await broadcast({
                "type": "roulette_progress",
                "data": {
                    "phase": "accelerating",
                    "wheel_rotation": round(progress * 720, 2),
                    "ball_position": round(-progress * 1080, 2),
                    "ball_radius": 100,
                    "progress": progress * 0.1
                }
            })
            await asyncio.sleep(0.05)

    async def _run_spinning_phase(self, broadcast: Callable[[dict], Any]) -> None:
        """Phase 2: Constant speed spinning."""
        duration = 2.0
        wheel_rotation = 720
        ball_position = -1080
        wheel_velocity = 1440  # degrees per second
        ball_velocity = -2160
        
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < duration:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            wheel_rotation += wheel_velocity * 0.05
            ball_position += ball_velocity * 0.05
            
            await broadcast({
                "type": "roulette_progress",
                "data": {
                    "phase": "spinning",
                    "wheel_rotation": round(wheel_rotation % 360, 2),
                    "ball_position": round(ball_position % 360, 2),
                    "ball_radius": 100,
                    "progress": 0.1 + (elapsed / duration) * 0.3
                }
            })
            await asyncio.sleep(0.05)

    async def _run_deceleration_phase(
        self,
        broadcast: Callable[[dict], Any],
        target_wheel_rotation: float,
        winning_index: int,
        pocket_angle: float,
        ball_offset: float
    ) -> None:
        """Phase 3: Wheel slows, ball drops."""
        duration = 3.5
        current_wheel_pos = 720 % 360
        rotations_needed = 3
        total_rotation_needed = rotations_needed * 360 + (target_wheel_rotation - current_wheel_pos) % 360
        
        ball_velocity = -1080 / 0.5
        
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < duration:
            elapsed = asyncio.get_event_loop().time() - start_time
            t = elapsed / duration
            ease = 1 - math.pow(1 - t, 3)
            
            wheel_rotation = current_wheel_pos + total_rotation_needed * ease
            ball_velocity *= 0.985
            ball_position = -1080 + ball_velocity * elapsed
            ball_radius = 100 - (ease * 40) + random.uniform(-2, 2)
            
            await broadcast({
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

    async def _run_settling_phase(
        self,
        broadcast: Callable[[dict], Any],
        target_wheel_rotation: float,
        winning_index: int,
        pocket_angle: float,
        ball_offset: float
    ) -> None:
        """Phase 4: Ball settles into pocket."""
        duration = 1.0
        final_wheel_pos = target_wheel_rotation % 360
        
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < duration:
            elapsed = asyncio.get_event_loop().time() - start_time
            t = elapsed / duration
            
            bounce = math.sin(t * math.pi * 4) * (1 - t) * 3
            wheel_rotation = final_wheel_pos + bounce
            ball_position = (winning_index * pocket_angle) + ball_offset + bounce
            
            await broadcast({
                "type": "roulette_ball_settling",
                "data": {
                    "phase": "settling",
                    "wheel_rotation": round(wheel_rotation, 2),
                    "ball_position": round(ball_position, 2),
                    "ball_radius": 60,
                    "progress": 0.8 + t * 0.15
                }
            })
            await asyncio.sleep(0.05)

    def _find_winning_option(self, room: GameRoom, winning_number: int) -> Optional[str]:
        """Find the bet option corresponding to the winning number."""
        for opt in room.bet_options:
            if opt.label == str(winning_number) or opt.id == str(winning_number):
                return opt.id
        # Fallback to first option
        return room.bet_options[0].id if room.bet_options else None

    def check_win(self, bet: Bet, winning_number: int) -> bool:
        """Check if a roulette bet wins."""
        bet_type = bet.bet_type
        
        if not bet_type:
            return bet.option_id == str(winning_number)
        
        if bet_type == RouletteBetType.SINGLE:
            return bet.bet_number == winning_number
        
        color = ROULETTE_COLORS.get(winning_number, "green")
        
        checks = {
            RouletteBetType.RED: lambda: color == "red",
            RouletteBetType.BLACK: lambda: color == "black",
            RouletteBetType.EVEN: lambda: winning_number not in [0, 37] and winning_number % 2 == 0,
            RouletteBetType.ODD: lambda: winning_number not in [0, 37] and winning_number % 2 == 1,
            RouletteBetType.LOW: lambda: 1 <= winning_number <= 18,
            RouletteBetType.HIGH: lambda: 19 <= winning_number <= 36,
            RouletteBetType.FIRST_DOZEN: lambda: 1 <= winning_number <= 12,
            RouletteBetType.SECOND_DOZEN: lambda: 13 <= winning_number <= 24,
            RouletteBetType.THIRD_DOZEN: lambda: 25 <= winning_number <= 36,
            RouletteBetType.FIRST_COLUMN: lambda: winning_number not in [0, 37] and winning_number % 3 == 1,
            RouletteBetType.SECOND_COLUMN: lambda: winning_number not in [0, 37] and winning_number % 3 == 2,
            RouletteBetType.THIRD_COLUMN: lambda: winning_number not in [0, 37] and winning_number % 3 == 0,
        }
        
        check_func = checks.get(bet_type)
        return check_func() if check_func else False

    def get_payout_multiplier(self, bet: Bet) -> int:
        """Get payout multiplier for a roulette bet."""
        bet_type = bet.bet_type or RouletteBetType.SINGLE
        return ROULETTE_PAYOUTS.get(bet_type, 35)

    @staticmethod
    def get_preset_options() -> list[dict]:
        """Get the standard roulette betting options."""
        options = [
            # Individual numbers
            {"id": "0", "label": "0", "odds": 36},
            {"id": "00", "label": "00", "odds": 36},
            *[{"id": str(i), "label": str(i), "odds": 36} for i in range(1, 37)],
            # Even money bets
            {"id": "red", "label": "Red", "odds": 2},
            {"id": "black", "label": "Black", "odds": 2},
            {"id": "even", "label": "Even", "odds": 2},
            {"id": "odd", "label": "Odd", "odds": 2},
            {"id": "1-18", "label": "1-18 (Low)", "odds": 2},
            {"id": "19-36", "label": "19-36 (High)", "odds": 2},
            # Dozens
            {"id": "1st12", "label": "1st 12", "odds": 3},
            {"id": "2nd12", "label": "2nd 12", "odds": 3},
            {"id": "3rd12", "label": "3rd 12", "odds": 3},
            # Columns
            {"id": "col1", "label": "Column 1", "odds": 3},
            {"id": "col2", "label": "Column 2", "odds": 3},
            {"id": "col3", "label": "Column 3", "odds": 3},
        ]
        return options
