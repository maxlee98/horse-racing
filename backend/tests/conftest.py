"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from typing import Generator

from core.models import GameRoom, GameStatus, GameMode, Player, Bet, BetOption
from core.constants import GameConstants
from repositories import InMemoryRoomRepository
from services import RoomService, BettingService, PlayerService
from game_modes import RouletteMode, HorseRacingMode, StandardGameMode, get_game_mode


@pytest.fixture
def mock_repo() -> Generator[InMemoryRoomRepository, None, None]:
    """Provide a fresh in-memory repository."""
    repo = InMemoryRoomRepository()
    yield repo
    # Cleanup: clear all rooms after test
    for room_id in list(repo._rooms.keys()):
        repo.delete(room_id)


@pytest.fixture
def room_service(mock_repo: InMemoryRoomRepository) -> RoomService:
    """Provide a RoomService with mock repository."""
    return RoomService(mock_repo)


@pytest.fixture
def betting_service(room_service: RoomService) -> BettingService:
    """Provide a BettingService."""
    return BettingService(room_service)


@pytest.fixture
def player_service(room_service: RoomService) -> PlayerService:
    """Provide a PlayerService."""
    return PlayerService(room_service)


@pytest.fixture
def sample_room(room_service: RoomService) -> GameRoom:
    """Create a sample room with basic bet options."""
    return room_service.create_room(
        host_id="host-1",
        title="Test Room",
        description="A test room",
        bet_options=[
            {"id": "1", "label": "Team A", "odds": 2.0},
            {"id": "2", "label": "Team B", "odds": 1.5},
        ],
        game_mode=GameMode.STANDARD,
    )


@pytest.fixture
def roulette_room(room_service: RoomService) -> GameRoom:
    """Create a roulette room with full bet options."""
    return room_service.create_room(
        host_id="host-1",
        title="Roulette Test",
        description="Roulette room for testing",
        bet_options=RouletteMode.get_preset_options(),
        game_mode=GameMode.ROULETTE,
    )


@pytest.fixture
def horse_racing_room(room_service: RoomService) -> GameRoom:
    """Create a horse racing room."""
    return room_service.create_room(
        host_id="host-1",
        title="Horse Racing Test",
        description="Horse racing room",
        bet_options=[
            {"id": "1", "label": "Horse A", "odds": 2.5},
            {"id": "2", "label": "Horse B", "odds": 3.0},
            {"id": "3", "label": "Horse C", "odds": 2.0},
        ],
        game_mode=GameMode.HORSE_RACING,
        use_randomized_probabilities=True,
    )


@pytest.fixture
def sample_player() -> Player:
    """Create a sample player."""
    return Player(
        id="player-1",
        name="Test Player",
        balance=GameConstants.DEFAULT_BALANCE,
        is_connected=True,
    )


@pytest.fixture
def roulette_mode() -> RouletteMode:
    """Provide a RouletteMode instance."""
    return RouletteMode()


@pytest.fixture
def horse_racing_mode() -> HorseRacingMode:
    """Provide a HorseRacingMode instance."""
    return HorseRacingMode()


@pytest.fixture
def standard_mode() -> StandardGameMode:
    """Provide a StandardGameMode instance."""
    return StandardGameMode()
