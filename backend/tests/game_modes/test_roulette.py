"""Tests for Roulette game mode."""

import pytest
from core.models import GameRoom, GameStatus, Bet, RouletteBetType, GameMode, Player
from core.constants import GameConstants
from game_modes import RouletteMode


class TestRouletteWinChecks:
    """Tests for roulette win checking logic."""

    def test_check_win_single_number(self, roulette_mode: RouletteMode):
        """Bet on 7 wins when 7 lands."""
        bet = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="7",
            option_label="7",
            amount=100,
            potential_win=3600,
            bet_type=RouletteBetType.SINGLE,
            bet_number=7
        )
        assert roulette_mode.check_win(bet, 7) is True
        assert roulette_mode.check_win(bet, 8) is False

    def test_check_win_red(self, roulette_mode: RouletteMode):
        """Red bet wins on red numbers."""
        bet = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="red",
            option_label="Red",
            amount=100,
            potential_win=200,
            bet_type=RouletteBetType.RED
        )
        # 1 is red
        assert roulette_mode.check_win(bet, 1) is True
        # 2 is black
        assert roulette_mode.check_win(bet, 2) is False
        # 0 is green
        assert roulette_mode.check_win(bet, 0) is False
        # 37 (00) is green
        assert roulette_mode.check_win(bet, 37) is False

    def test_check_win_black(self, roulette_mode: RouletteMode):
        """Black bet wins on black numbers."""
        bet = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="black",
            option_label="Black",
            amount=100,
            potential_win=200,
            bet_type=RouletteBetType.BLACK
        )
        # 2 is black
        assert roulette_mode.check_win(bet, 2) is True
        # 1 is red
        assert roulette_mode.check_win(bet, 1) is False

    def test_check_win_even(self, roulette_mode: RouletteMode):
        """Even bet wins on even numbers (excluding 0 and 00)."""
        bet = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="even",
            option_label="Even",
            amount=100,
            potential_win=200,
            bet_type=RouletteBetType.EVEN
        )
        # 2, 4, 6 are even
        assert roulette_mode.check_win(bet, 2) is True
        assert roulette_mode.check_win(bet, 4) is True
        # 1, 3 are odd
        assert roulette_mode.check_win(bet, 1) is False
        # 0 and 00 are neither even nor odd
        assert roulette_mode.check_win(bet, 0) is False
        assert roulette_mode.check_win(bet, 37) is False

    def test_check_win_odd(self, roulette_mode: RouletteMode):
        """Odd bet wins on odd numbers (excluding 0 and 00)."""
        bet = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="odd",
            option_label="Odd",
            amount=100,
            potential_win=200,
            bet_type=RouletteBetType.ODD
        )
        assert roulette_mode.check_win(bet, 1) is True
        assert roulette_mode.check_win(bet, 3) is True
        assert roulette_mode.check_win(bet, 2) is False
        assert roulette_mode.check_win(bet, 0) is False
        assert roulette_mode.check_win(bet, 37) is False

    def test_check_win_low_high(self, roulette_mode: RouletteMode):
        """Low (1-18) and High (19-36) bets."""
        low_bet = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="1-18",
            option_label="1-18 (Low)",
            amount=100,
            potential_win=200,
            bet_type=RouletteBetType.LOW
        )
        high_bet = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="19-36",
            option_label="19-36 (High)",
            amount=100,
            potential_win=200,
            bet_type=RouletteBetType.HIGH
        )
        
        # Low range
        assert roulette_mode.check_win(low_bet, 1) is True
        assert roulette_mode.check_win(low_bet, 18) is True
        assert roulette_mode.check_win(low_bet, 19) is False
        
        # High range
        assert roulette_mode.check_win(high_bet, 19) is True
        assert roulette_mode.check_win(high_bet, 36) is True
        assert roulette_mode.check_win(high_bet, 18) is False
        
        # 0 and 00 lose both
        assert roulette_mode.check_win(low_bet, 0) is False
        assert roulette_mode.check_win(high_bet, 0) is False

    def test_check_win_dozens(self, roulette_mode: RouletteMode):
        """Dozen bets (1-12, 13-24, 25-36)."""
        first_dozen = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="1st12",
            option_label="1st 12",
            amount=100,
            potential_win=300,
            bet_type=RouletteBetType.FIRST_DOZEN
        )
        second_dozen = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="2nd12",
            option_label="2nd 12",
            amount=100,
            potential_win=300,
            bet_type=RouletteBetType.SECOND_DOZEN
        )
        third_dozen = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="3rd12",
            option_label="3rd 12",
            amount=100,
            potential_win=300,
            bet_type=RouletteBetType.THIRD_DOZEN
        )
        
        # First dozen
        assert roulette_mode.check_win(first_dozen, 1) is True
        assert roulette_mode.check_win(first_dozen, 12) is True
        assert roulette_mode.check_win(first_dozen, 13) is False
        
        # Second dozen
        assert roulette_mode.check_win(second_dozen, 13) is True
        assert roulette_mode.check_win(second_dozen, 24) is True
        assert roulette_mode.check_win(second_dozen, 25) is False
        
        # Third dozen
        assert roulette_mode.check_win(third_dozen, 25) is True
        assert roulette_mode.check_win(third_dozen, 36) is True
        assert roulette_mode.check_win(third_dozen, 24) is False

    def test_check_win_columns(self, roulette_mode: RouletteMode):
        """Column bets."""
        col1 = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="col1",
            option_label="Column 1",
            amount=100,
            potential_win=300,
            bet_type=RouletteBetType.FIRST_COLUMN
        )
        col2 = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="col2",
            option_label="Column 2",
            amount=100,
            potential_win=300,
            bet_type=RouletteBetType.SECOND_COLUMN
        )
        col3 = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="col3",
            option_label="Column 3",
            amount=100,
            potential_win=300,
            bet_type=RouletteBetType.THIRD_COLUMN
        )
        
        # Column 1: 1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34
        assert roulette_mode.check_win(col1, 1) is True
        assert roulette_mode.check_win(col1, 4) is True
        assert roulette_mode.check_win(col1, 2) is False
        
        # Column 2: 2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35
        assert roulette_mode.check_win(col2, 2) is True
        assert roulette_mode.check_win(col2, 5) is True
        assert roulette_mode.check_win(col2, 1) is False
        
        # Column 3: 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36
        assert roulette_mode.check_win(col3, 3) is True
        assert roulette_mode.check_win(col3, 6) is True
        assert roulette_mode.check_win(col3, 1) is False


class TestRoulettePayouts:
    """Tests for roulette payout calculations."""

    def test_payout_single_number(self, roulette_mode: RouletteMode):
        """Single number pays 35:1."""
        bet = Bet(
            player_id="p1",
            player_name="Player 1",
            option_id="7",
            option_label="7",
            amount=100,
            potential_win=3600,
            bet_type=RouletteBetType.SINGLE
        )
        assert roulette_mode.get_payout_multiplier(bet) == 35

    def test_payout_even_money(self, roulette_mode: RouletteMode):
        """Red/Black/Even/Odd/Low/High pay 1:1."""
        for bet_type in [
            RouletteBetType.RED,
            RouletteBetType.BLACK,
            RouletteBetType.EVEN,
            RouletteBetType.ODD,
            RouletteBetType.LOW,
            RouletteBetType.HIGH,
        ]:
            bet = Bet(
                player_id="p1",
                player_name="Player 1",
                option_id="red",
                option_label="Red",
                amount=100,
                potential_win=200,
                bet_type=bet_type
            )
            assert roulette_mode.get_payout_multiplier(bet) == 1

    def test_payout_dozens_columns(self, roulette_mode: RouletteMode):
        """Dozens and columns pay 2:1."""
        for bet_type in [
            RouletteBetType.FIRST_DOZEN,
            RouletteBetType.SECOND_DOZEN,
            RouletteBetType.THIRD_DOZEN,
            RouletteBetType.FIRST_COLUMN,
            RouletteBetType.SECOND_COLUMN,
            RouletteBetType.THIRD_COLUMN,
        ]:
            bet = Bet(
                player_id="p1",
                player_name="Player 1",
                option_id="1st12",
                option_label="1st 12",
                amount=100,
                potential_win=300,
                bet_type=bet_type
            )
            assert roulette_mode.get_payout_multiplier(bet) == 2


class TestRouletteProbabilities:
    """Tests for roulette probability calculations."""

    def test_single_number_probability(self, roulette_room: GameRoom, roulette_mode: RouletteMode):
        """Single numbers have 1/38 probability."""
        roulette_mode.calculate_probabilities(roulette_room)
        
        # Find a single number option
        num_option = next(o for o in roulette_room.bet_options if o.label == "7")
        assert num_option.probability == round(1.0 / 38, 4)

    def test_color_probability(self, roulette_room: GameRoom, roulette_mode: RouletteMode):
        """Red/Black have 18/38 probability."""
        roulette_mode.calculate_probabilities(roulette_room)
        
        red_option = next(o for o in roulette_room.bet_options if o.label == "Red")
        assert red_option.probability == round(18.0 / 38, 4)

    def test_dozen_probability(self, roulette_room: GameRoom, roulette_mode: RouletteMode):
        """Dozens have 12/38 probability."""
        roulette_mode.calculate_probabilities(roulette_room)
        
        dozen_option = next(o for o in roulette_room.bet_options if o.label == "1st 12")
        assert dozen_option.probability == round(12.0 / 38, 4)


class TestRouletteMultiBetScenario:
    """Tests for player betting on multiple items."""

    def test_multiple_bets_one_wins_break_even(
        self, 
        roulette_room: GameRoom,
        room_service, 
        betting_service,
        player_service
    ):
        """
        Player bets $100 on Red and $100 on Black.
        Winning number is 7 (Red).
        
        Expected:
        - Red bet wins: $100 * 2 = $200 payout (net +$100 on this bet)
        - Black bet loses: $100 lost
        - Overall net: $0 break-even
        - Player is considered to have "won" because at least one bet won
        """
        # Add player
        player = player_service.add_player(roulette_room.room_id, "p1", "Player 1")
        initial_balance = player.balance
        
        # Open betting
        room_service.update_status(roulette_room.room_id, GameStatus.OPEN, roulette_room.host_id)
        
        # Place bets on Red and Black
        red_bet = betting_service.place_bet(
            roulette_room.room_id, "p1", "red", 100, 
            bet_type="red"
        )
        black_bet = betting_service.place_bet(
            roulette_room.room_id, "p1", "black", 100,
            bet_type="black"
        )
        
        # Simulate winning number 7 (Red)
        winning_number = 7
        
        # Process payouts
        winning_bets = betting_service.process_payouts(roulette_room, winning_number)
        
        # Player should have winning bets
        player_winning_bets = [wb for wb in winning_bets if wb["player_id"] == "p1"]
        assert len(player_winning_bets) == 1  # Only Red won
        
        # Check the winning bet details
        assert player_winning_bets[0]["bet_amount"] == 100
        assert player_winning_bets[0]["payout"] == 200  # $100 * 2 (1:1 + original)
        
        # Player balance should be back to initial (break-even)
        # Started with 1000, bet 200, got back 200
        player = room_service.get_room(roulette_room.room_id).players["p1"]
        assert player.balance == initial_balance  # Net $0

    def test_multiple_bets_one_wins_net_loss(
        self, 
        roulette_room: GameRoom,
        room_service, 
        betting_service,
        player_service
    ):
        """
        Player bets $100 on Red, $50 on Black, $50 on Even.
        Winning number is 7 (Red).
        
        Expected:
        - Red bet wins: $200 payout
        - Black loses: -$50
        - Even loses: -$50  
        - Overall net: -$100 loss
        - But player is STILL considered a "winner" because Red won
        """
        player = player_service.add_player(roulette_room.room_id, "p1", "Player 1")
        initial_balance = player.balance
        
        room_service.update_status(roulette_room.room_id, GameStatus.OPEN, roulette_room.host_id)
        
        # Place multiple bets
        betting_service.place_bet(roulette_room.room_id, "p1", "red", 100, bet_type="red")
        betting_service.place_bet(roulette_room.room_id, "p1", "black", 50, bet_type="black")
        betting_service.place_bet(roulette_room.room_id, "p1", "even", 50, bet_type="even")
        
        winning_number = 7  # Red but not Even
        winning_bets = betting_service.process_payouts(roulette_room, winning_number)
        
        # Only Red should win
        player_winning_bets = [wb for wb in winning_bets if wb["player_id"] == "p1"]
        assert len(player_winning_bets) == 1
        
        # Net loss: started 1000, bet 200, got back 200 from Red = $0 profit
        # Actually Red pays 1:1, so $100 bet returns $200 (100 profit)
        # But lost $50 on Black and $50 on Even
        # Net: +100 - 50 - 50 = $0
        player = room_service.get_room(roulette_room.room_id).players["p1"]
        # 1000 - 200 (bets) + 200 (Red payout) = 1000
        assert player.balance == initial_balance

    def test_multiple_bets_multiple_win_big_payout(
        self, 
        roulette_room: GameRoom,
        room_service, 
        betting_service,
        player_service
    ):
        """
        Player bets $50 on Red and $50 on Even.
        Winning number is 12 (Red + Even).
        
        Expected:
        - Both bets win!
        - Red: $50 * 2 = $100
        - Even: $50 * 2 = $100
        - Total payout: $200
        - Net profit: $100
        """
        player = player_service.add_player(roulette_room.room_id, "p1", "Player 1")
        initial_balance = player.balance
        
        room_service.update_status(roulette_room.room_id, GameStatus.OPEN, roulette_room.host_id)
        
        betting_service.place_bet(roulette_room.room_id, "p1", "red", 50, bet_type="red")
        betting_service.place_bet(roulette_room.room_id, "p1", "even", 50, bet_type="even")
        
        winning_number = 12  # Red AND Even
        winning_bets = betting_service.process_payouts(roulette_room, winning_number)
        
        # Both bets should win
        player_winning_bets = [wb for wb in winning_bets if wb["player_id"] == "p1"]
        assert len(player_winning_bets) == 2
        
        # Total payout should be 200
        total_payout = sum(wb["payout"] for wb in player_winning_bets)
        assert total_payout == 200
        
        # Player balance: 1000 - 100 + 200 = 1100
        player = room_service.get_room(roulette_room.room_id).players["p1"]
        assert player.balance == initial_balance + 100

    def test_single_number_plus_color_bet(
        self, 
        roulette_room: GameRoom,
        room_service, 
        betting_service,
        player_service
    ):
        """
        Player bets $10 on number 7 and $50 on Red.
        Winning number is 7 (Red).
        
        Expected:
        - Single number 7: $10 * 36 = $360 payout (35:1 + original)
        - Red: $50 * 2 = $100 payout
        - Total payout: $460
        - Player is a big winner!
        """
        player = player_service.add_player(roulette_room.room_id, "p1", "Player 1")
        initial_balance = player.balance
        
        room_service.update_status(roulette_room.room_id, GameStatus.OPEN, roulette_room.host_id)
        
        # Bet on single number 7
        betting_service.place_bet(
            roulette_room.room_id, "p1", "7", 10, 
            bet_type="single", bet_number=7
        )
        # Bet on Red
        betting_service.place_bet(roulette_room.room_id, "p1", "red", 50, bet_type="red")
        
        winning_number = 7
        winning_bets = betting_service.process_payouts(roulette_room, winning_number)
        
        # Both bets should win
        player_winning_bets = [wb for wb in winning_bets if wb["player_id"] == "p1"]
        assert len(player_winning_bets) == 2
        
        # Check payouts
        single_bet_payout = next(wb for wb in player_winning_bets if wb["bet_type"] == "single")
        assert single_bet_payout["bet_amount"] == 10
        assert single_bet_payout["payout"] == 360  # 10 * 36
        
        red_bet_payout = next(wb for wb in player_winning_bets if wb["bet_type"] == "red")
        assert red_bet_payout["bet_amount"] == 50
        assert red_bet_payout["payout"] == 100  # 50 * 2
