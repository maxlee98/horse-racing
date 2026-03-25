"""Tests for RoomService."""

import pytest
from core.models import GameRoom, GameStatus, GameMode, Player, BetOption, Bet
from core.constants import GameConstants
from core.exceptions import RoomNotFoundException, NotAuthorizedException


class TestCreateRoom:
    """Tests for room creation."""

    def test_create_room_success(self, room_service):
        """Room created with correct defaults."""
        room = room_service.create_room(
            host_id="host-1",
            title="Test Room",
            description="A test room",
            bet_options=[
                {"id": "1", "label": "Team A", "odds": 2.0},
                {"id": "2", "label": "Team B", "odds": 1.5},
            ],
            game_mode=GameMode.STANDARD,
        )
        
        assert room.host_id == "host-1"
        assert room.title == "Test Room"
        assert room.status == GameStatus.WAITING
        assert room.game_mode == GameMode.STANDARD
        assert len(room.bet_options) == 2
        assert room.max_players == GameConstants.MAX_PLAYERS
        assert len(room.room_id) == 8  # 8-character ID

    def test_create_room_with_roulette_preset(self, room_service):
        """Roulette room created with full bet options."""
        from game_modes import RouletteMode
        
        room = room_service.create_room(
            host_id="host-1",
            title="Roulette Room",
            description="A roulette room",
            bet_options=RouletteMode.get_preset_options(),
            game_mode=GameMode.ROULETTE,
        )
        
        assert room.game_mode == GameMode.ROULETTE
        # Should have 50 options (0, 00, 1-36, red, black, even, odd, 1-18, 19-36, 3 dozens, 3 columns)
        assert len(room.bet_options) == 50

    def test_create_room_probabilities_calculated(self, room_service):
        """Probabilities calculated on creation."""
        room = room_service.create_room(
            host_id="host-1",
            title="Test",
            description="A test room",
            bet_options=[
                {"id": "1", "label": "A", "odds": 2.0},
                {"id": "2", "label": "B", "odds": 2.0},
            ],
            game_mode=GameMode.STANDARD,
        )
        
        # Equal probability for 2 options
        assert room.bet_options[0].probability == 0.5
        assert room.bet_options[1].probability == 0.5


class TestGetRoom:
    """Tests for getting rooms."""

    def test_get_room_success(self, room_service, sample_room):
        """Get existing room."""
        room = room_service.get_room(sample_room.room_id)
        assert room is not None
        assert room.room_id == sample_room.room_id

    def test_get_room_not_found(self, room_service):
        """Get non-existent room returns None."""
        room = room_service.get_room("NONEXISTENT")
        assert room is None

    def test_get_room_or_raise_success(self, room_service, sample_room):
        """Get or raise with existing room."""
        room = room_service.get_room_or_raise(sample_room.room_id)
        assert room.room_id == sample_room.room_id

    def test_get_room_or_raise_not_found(self, room_service):
        """Get or raise with non-existent room raises exception."""
        with pytest.raises(RoomNotFoundException, match="Room NONEXISTENT not found"):
            room_service.get_room_or_raise("NONEXISTENT")


class TestUpdateStatus:
    """Tests for updating room status."""

    def test_update_status_success(self, room_service, sample_room):
        """Host can update status."""
        room = room_service.update_status(
            sample_room.room_id,
            GameStatus.OPEN,
            sample_room.host_id
        )
        assert room.status == GameStatus.OPEN

    def test_update_status_unauthorized(self, room_service, sample_room):
        """Non-host cannot update status."""
        with pytest.raises(NotAuthorizedException, match="Only host can update status"):
            room_service.update_status(
                sample_room.room_id,
                GameStatus.OPEN,
                "not-the-host"
            )


class TestSetWinner:
    """Tests for setting winner."""

    def test_set_winner_success(self, room_service, sample_room):
        """Host can set winner."""
        room = room_service.set_winner(
            sample_room.room_id,
            "1",
            sample_room.host_id
        )
        assert room.winner_option_id == "1"
        assert room.status == GameStatus.ENDED

    def test_set_winner_invalid_option(self, room_service, sample_room):
        """Cannot set invalid option as winner."""
        with pytest.raises(ValueError, match="Invalid option: invalid-id"):
            room_service.set_winner(
                sample_room.room_id,
                "invalid-id",
                sample_room.host_id
            )

    def test_set_winner_unauthorized(self, room_service, sample_room):
        """Non-host cannot set winner."""
        with pytest.raises(NotAuthorizedException, match="Only host can set winner"):
            room_service.set_winner(
                sample_room.room_id,
                "1",
                "not-the-host"
            )


class TestUpdateProbabilities:
    """Tests for updating probabilities."""

    def test_update_probabilities_success(self, room_service, sample_room):
        """Host can update probabilities."""
        room = room_service.update_probabilities(
            sample_room.room_id,
            {"1": 0.7, "2": 0.3},
            sample_room.host_id
        )
        
        assert room.bet_options[0].probability == 0.7
        assert room.bet_options[1].probability == 0.3

    def test_update_probabilities_clamped(self, room_service, sample_room):
        """Probabilities clamped to valid range."""
        room = room_service.update_probabilities(
            sample_room.room_id,
            {"1": 1.5, "2": -0.5},  # Invalid values
            sample_room.host_id
        )
        
        # Should be clamped to valid range
        assert room.bet_options[0].probability <= 1.0
        assert room.bet_options[1].probability >= 0.01

    def test_update_probabilities_unauthorized(self, room_service, sample_room):
        """Non-host cannot update probabilities."""
        with pytest.raises(NotAuthorizedException, match="Only host can update probabilities"):
            room_service.update_probabilities(
                sample_room.room_id,
                {"1": 0.5, "2": 0.5},
                "not-the-host"
            )


class TestRandomizeProbabilities:
    """Tests for randomizing probabilities."""

    def test_randomize_probabilities_sum_to_one(self, room_service, sample_room):
        """Randomized probabilities sum to 1."""
        room = room_service.randomize_probabilities(
            sample_room.room_id,
            sample_room.host_id
        )
        
        total = sum(opt.probability for opt in room.bet_options)
        assert abs(total - 1.0) < 0.001  # Allow floating point error

    def test_randomize_probabilities_unauthorized(self, room_service, sample_room):
        """Non-host cannot randomize."""
        with pytest.raises(NotAuthorizedException, match="Only host can randomize"):
            room_service.randomize_probabilities(
                sample_room.room_id,
                "not-the-host"
            )


class TestNextRound:
    """Tests for starting next round."""

    def test_next_round_clears_state(self, room_service, sample_room):
        """Next round clears bets and winner."""
        # Setup: Add some bets and set a winner
        sample_room.bets.append(Player(id="p1", name="P1", balance=100, is_connected=True))
        sample_room.winner_option_id = "1"
        sample_room.status = GameStatus.ENDED
        room_service._repo.save(sample_room)
        
        room = room_service.next_round(
            sample_room.room_id,
            sample_room.host_id
        )
        
        assert len(room.bets) == 0
        assert room.winner_option_id is None
        assert room.status == GameStatus.WAITING
        assert room.round_number == 2


class TestResetLobby:
    """Tests for resetting lobby."""

    def test_reset_lobby_full_reset(self, room_service, sample_room):
        """Reset clears everything."""
        # Setup: Add players with spent balances
        sample_room.players["p1"] = Player(id="p1", name="P1", balance=500, is_connected=True)
        sample_room.bets.append(Player(id="p1", name="P1", balance=100, is_connected=True))
        sample_room.winner_option_id = "1"
        sample_room.round_number = 5
        room_service._repo.save(sample_room)
        
        room = room_service.reset_lobby(
            sample_room.room_id,
            sample_room.host_id
        )
        
        assert room.status == GameStatus.WAITING
        assert len(room.bets) == 0
        assert room.winner_option_id is None
        assert room.round_number == 1
        assert room.players["p1"].balance == GameConstants.DEFAULT_BALANCE


class TestToDict:
    """Tests for room serialization."""

    def test_to_dict_contains_required_fields(self, room_service, sample_room):
        """Serialization includes all required fields."""
        data = room_service.to_dict(sample_room)
        
        required_fields = [
            "room_id", "title", "description", "status",
            "bet_options", "players", "bets", "winner_option_id",
            "max_players", "player_count", "game_mode", "round_number",
            "use_randomized_probabilities"
        ]
        
        for field in required_fields:
            assert field in data


class TestChangeGame:
    """Tests for changing game modes."""

    def test_change_game_success(self, room_service, sample_room):
        """Host can change game mode from standard to horse racing."""
        room = room_service.change_game(
            sample_room.room_id,
            GameMode.HORSE_RACING,
            sample_room.host_id
        )
        
        assert room.game_mode == GameMode.HORSE_RACING
        assert room.status == GameStatus.WAITING
        # Should have horse racing default options
        assert len(room.bet_options) == 5
        assert room.bet_options[0].label == "Thunder Bolt"

    def test_change_game_to_roulette(self, room_service, sample_room):
        """Host can change game mode to roulette."""
        room = room_service.change_game(
            sample_room.room_id,
            GameMode.ROULETTE,
            sample_room.host_id
        )
        
        assert room.game_mode == GameMode.ROULETTE
        assert room.status == GameStatus.WAITING
        # Should have full roulette preset options (50 options)
        assert len(room.bet_options) == 50

    def test_change_game_clears_bets(self, room_service, sample_room):
        """Changing game clears existing bets."""
        # Setup: Add some bets
        sample_room.bets = [Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="1",
            option_label="Team A",
            amount=100,
            potential_win=200
        )]
        room_service._repo.save(sample_room)
        
        room = room_service.change_game(
            sample_room.room_id,
            GameMode.HORSE_RACING,
            sample_room.host_id
        )
        
        assert len(room.bets) == 0

    def test_change_game_clears_winner(self, room_service, sample_room):
        """Changing game clears winner."""
        # Setup: Set a winner
        sample_room.winner_option_id = "1"
        sample_room.status = GameStatus.ENDED
        room_service._repo.save(sample_room)
        
        room = room_service.change_game(
            sample_room.room_id,
            GameMode.HORSE_RACING,
            sample_room.host_id
        )
        
        assert room.winner_option_id is None
        assert room.status == GameStatus.WAITING

    def test_change_game_preserves_player_balances(self, room_service, sample_room):
        """Player balances are preserved when changing games."""
        # Setup: Add players with spent balances
        sample_room.players["p1"] = Player(id="p1", name="P1", balance=500, is_connected=True)
        sample_room.players["p2"] = Player(id="p2", name="P2", balance=750, is_connected=True)
        room_service._repo.save(sample_room)
        
        room = room_service.change_game(
            sample_room.room_id,
            GameMode.HORSE_RACING,
            sample_room.host_id
        )
        
        assert room.players["p1"].balance == 500
        assert room.players["p2"].balance == 750

    def test_change_game_clears_roulette_history(self, room_service):
        """Roulette history is cleared when leaving roulette mode."""
        # Create a roulette room
        room = room_service.create_room(
            host_id="host-1",
            title="Roulette Room",
            description="",
            bet_options=[],
            game_mode=GameMode.ROULETTE,
        )
        room.roulette_history = ["7", "12", "00"]
        room_service._repo.save(room)
        
        # Change to horse racing
        updated_room = room_service.change_game(
            room.room_id,
            GameMode.HORSE_RACING,
            "host-1"
        )
        
        assert len(updated_room.roulette_history) == 0

    def test_change_game_blocked_when_locked(self, room_service, sample_room):
        """Cannot change game while game is in progress."""
        sample_room.status = GameStatus.LOCKED
        room_service._repo.save(sample_room)
        
        from core.exceptions import InvalidOperationException
        with pytest.raises(InvalidOperationException, match="Cannot change game while game is in progress"):
            room_service.change_game(
                sample_room.room_id,
                GameMode.HORSE_RACING,
                sample_room.host_id
            )

    def test_change_game_unauthorized(self, room_service, sample_room):
        """Non-host cannot change game."""
        with pytest.raises(NotAuthorizedException, match="Only host can change game mode"):
            room_service.change_game(
                sample_room.room_id,
                GameMode.HORSE_RACING,
                "not-the-host"
            )

    def test_change_game_recalculates_probabilities(self, room_service, sample_room):
        """Probabilities are recalculated for new game mode."""
        room = room_service.change_game(
            sample_room.room_id,
            GameMode.HORSE_RACING,
            sample_room.host_id
        )
        
        # Horse racing uses inverse odds for probability calculation
        # Thunder Bolt has odds 2.5, so probability = 1/2.5 = 0.4
        assert room.bet_options[0].probability > 0
        assert sum(opt.probability for opt in room.bet_options) == pytest.approx(1.0, rel=0.01)
