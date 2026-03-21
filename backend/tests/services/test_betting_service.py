"""Tests for BettingService."""

import pytest
from core.models import GameRoom, GameStatus, Bet, BetOption, GameMode, Player
from core.constants import GameConstants
from core.exceptions import InvalidBetException, RoomNotFoundException
from services import BettingService, RoomService
from repositories import InMemoryRoomRepository


class TestPlaceBet:
    """Tests for placing bets."""

    def test_place_bet_success(self, room_service, betting_service, sample_room):
        """Successful bet deducts balance and creates bet."""
        # Add player
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        
        # Open betting
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        initial_balance = sample_room.players["p1"].balance
        
        # Place bet
        bet = betting_service.place_bet(sample_room.room_id, "p1", "1", 100)
        
        # Assertions
        assert bet.player_id == "p1"
        assert bet.option_id == "1"
        assert bet.amount == 100
        assert bet.potential_win == 200  # 100 * 2.0 odds
        
        # Balance deducted
        updated_room = room_service.get_room(sample_room.room_id)
        assert updated_room.players["p1"].balance == initial_balance - 100

    def test_place_bet_insufficient_balance(self, room_service, betting_service, sample_room):
        """Cannot bet more than balance."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=50, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        with pytest.raises(InvalidBetException, match="Insufficient balance"):
            betting_service.place_bet(sample_room.room_id, "p1", "1", 100)

    def test_place_bet_when_locked(self, room_service, betting_service, sample_room):
        """Cannot bet when betting is locked."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        # Status is WAITING by default
        
        with pytest.raises(InvalidBetException, match="Betting is not open"):
            betting_service.place_bet(sample_room.room_id, "p1", "1", 100)

    def test_place_bet_invalid_amount(self, room_service, betting_service, sample_room):
        """Cannot bet zero or negative."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        with pytest.raises(InvalidBetException, match="Invalid bet amount"):
            betting_service.place_bet(sample_room.room_id, "p1", "1", 0)
        
        with pytest.raises(InvalidBetException, match="Invalid bet amount"):
            betting_service.place_bet(sample_room.room_id, "p1", "1", -50)

    def test_place_bet_duplicate_option(self, room_service, betting_service, sample_room):
        """Cannot bet twice on same option."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        # First bet succeeds
        betting_service.place_bet(sample_room.room_id, "p1", "1", 50)
        
        # Second bet on same option fails
        with pytest.raises(InvalidBetException, match="Already placed a bet on this option"):
            betting_service.place_bet(sample_room.room_id, "p1", "1", 50)

    def test_place_bet_invalid_option(self, room_service, betting_service, sample_room):
        """Cannot bet on non-existent option."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        with pytest.raises(InvalidBetException, match="Invalid option"):
            betting_service.place_bet(sample_room.room_id, "p1", "invalid-id", 50)

    def test_place_bet_room_not_found(self, betting_service):
        """Cannot bet in non-existent room."""
        with pytest.raises(RoomNotFoundException):
            betting_service.place_bet("NONEXISTENT", "p1", "1", 50)


class TestProcessPayouts:
    """Tests for processing payouts."""

    def test_process_payouts_winner_gets_paid(self, room_service, betting_service, sample_room):
        """Winner receives correct payout."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        # Place bet
        betting_service.place_bet(sample_room.room_id, "p1", "1", 100)
        initial_balance = sample_room.players["p1"].balance  # 900 after bet
        
        # Process payout for option "1"
        winning_bets = betting_service.process_payouts(sample_room, "1")
        
        # Assertions
        assert len(winning_bets) == 1
        assert winning_bets[0]["player_id"] == "p1"
        assert winning_bets[0]["payout"] == 200  # 100 * 2.0
        
        # Player balance updated
        updated_room = room_service.get_room(sample_room.room_id)
        assert updated_room.players["p1"].balance == 900 + 200

    def test_process_payouts_loser_gets_nothing(self, room_service, betting_service, sample_room):
        """Loser receives no payout."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        # Bet on option 1, but winner is option 2
        betting_service.place_bet(sample_room.room_id, "p1", "1", 100)
        initial_balance = sample_room.players["p1"].balance  # 900
        
        # Process payout for option "2"
        winning_bets = betting_service.process_payouts(sample_room, "2")
        
        # No winning bets
        assert len(winning_bets) == 0
        
        # Player balance unchanged (lost the bet)
        updated_room = room_service.get_room(sample_room.room_id)
        assert updated_room.players["p1"].balance == initial_balance

    def test_process_payouts_multiple_winners(self, room_service, betting_service, sample_room):
        """Multiple winners all get paid."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        sample_room.players["p2"] = Player(
            id="p2", name="Player 2", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        # Both bet on option 1
        betting_service.place_bet(sample_room.room_id, "p1", "1", 100)
        betting_service.place_bet(sample_room.room_id, "p2", "1", 200)
        
        # Process payout
        winning_bets = betting_service.process_payouts(sample_room, "1")
        
        # Both should be winners
        assert len(winning_bets) == 2
        payouts = {wb["player_id"]: wb["payout"] for wb in winning_bets}
        assert payouts["p1"] == 200  # 100 * 2.0
        assert payouts["p2"] == 400  # 200 * 2.0


class TestBetQueries:
    """Tests for bet query methods."""

    def test_get_player_bets(self, room_service, betting_service, sample_room):
        """Get all bets by a player."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        sample_room.players["p2"] = Player(
            id="p2", name="Player 2", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        betting_service.place_bet(sample_room.room_id, "p1", "1", 100)
        betting_service.place_bet(sample_room.room_id, "p2", "2", 200)
        
        p1_bets = betting_service.get_player_bets(sample_room, "p1")
        assert len(p1_bets) == 1
        assert p1_bets[0].amount == 100

    def test_get_total_bet_amount(self, room_service, betting_service, sample_room):
        """Get total amount bet in room."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        sample_room.players["p2"] = Player(
            id="p2", name="Player 2", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        betting_service.place_bet(sample_room.room_id, "p1", "1", 100)
        betting_service.place_bet(sample_room.room_id, "p2", "2", 200)
        
        total = betting_service.get_total_bet_amount(sample_room)
        assert total == 300

    def test_get_bets_on_option(self, room_service, betting_service, sample_room):
        """Get all bets on a specific option."""
        room_service._repo.save(sample_room)
        sample_room.players["p1"] = Player(
            id="p1", name="Player 1", balance=1000, is_connected=True
        )
        sample_room.players["p2"] = Player(
            id="p2", name="Player 2", balance=1000, is_connected=True
        )
        room_service._repo.save(sample_room)
        room_service.update_status(sample_room.room_id, GameStatus.OPEN, sample_room.host_id)
        
        betting_service.place_bet(sample_room.room_id, "p1", "1", 100)
        betting_service.place_bet(sample_room.room_id, "p2", "1", 200)
        
        option_1_bets = betting_service.get_bets_on_option(sample_room, "1")
        assert len(option_1_bets) == 2
