export type GameStatus = 'waiting' | 'open' | 'locked' | 'ended';
export type GameMode = 'standard' | 'horse_racing' | 'roulette';

export type RouletteBetType =
  | 'single'
  | 'red'
  | 'black'
  | 'even'
  | 'odd'
  | 'low'
  | 'high'
  | 'first_dozen'
  | 'second_dozen'
  | 'third_dozen'
  | 'first_column'
  | 'second_column'
  | 'third_column';

export interface BetOption {
  id: string;
  label: string;
  odds: number;
  probability: number;  // Win probability (0-1)
}

export interface RacePosition {
  option_id: string;
  label: string;
  position: number;  // 0-100 race progress
  probability: number;
  rank?: number;  // Position in race (1st, 2nd, etc.)
  finish_time?: number;  // Time in seconds to finish
  is_winner?: boolean;  // Whether this horse is the winner
  momentum?: number;        // Momentum factor: -0.2 to +0.3 range
  momentum_surge?: boolean; // True if momentum > 0.2 (significant speed burst)
}

export interface RaceResults {
  positions: RacePosition[];
  race_duration: number;
  winner_id: string;
  winner_label: string;
}

export interface Player {
  id: string;
  name: string;
  balance: number;
  is_connected: boolean;
}

export interface Bet {
  player_id: string;
  player_name: string;
  option_id: string;
  option_label: string;
  amount: number;
  potential_win: number;
  bet_type?: RouletteBetType;
  bet_number?: number;
}

export interface RouletteState {
  is_spinning: boolean;
  wheel_rotation: number;
  ball_position: number;
  ball_radius: number;
  winning_number: string | null;
  winning_color: 'red' | 'black' | 'green' | null;
  phase: 'accelerating' | 'spinning' | 'decelerating' | 'settling' | 'revealing' | null;
  progress: number;
  countdown?: number;
  message?: string;
  total_payout?: number;
  winning_bets?: Array<{
    player_id: string;
    player_name: string;
    bet_amount: number;
    payout: number;
    bet_type: string;
  }>;
}

export interface RoomState {
  room_id: string;
  title: string;
  description: string;
  status: GameStatus;
  bet_options: BetOption[];
  players: Record<string, Player>;
  bets: Bet[];
  winner_option_id: string | null;
  max_players: number;
  player_count: number;
  game_mode: GameMode;
  round_number: number;
  use_randomized_probabilities: boolean;
  roulette_history?: string[];
}

export interface RaceState {
  is_racing: boolean;
  positions: RacePosition[];
  progress: number;
  winner_id: string | null;
  countdown?: number;
  message?: string;
}

export type WSMessageType =
  | 'join'
  | 'place_bet'
  | 'host_action'
  | 'room_state'
  | 'player_joined'
  | 'player_left'
  | 'bet_placed'
  | 'game_updated'
  | 'game_ended'
  | 'error'
  | 'race_started'
  | 'race_progress'
  | 'race_ended'
  | 'roulette_started'
  | 'roulette_progress'
  | 'roulette_ball_settling'
  | 'roulette_ended'
  | 'game_mode_changed';

// American Roulette constants
export const AMERICAN_ROULETTE_ORDER = [
  0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1,
  37, // 00 represented as 37
  27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16, 4, 23, 35, 14, 2
];

export const ROULETTE_COLORS: Record<number, 'red' | 'black' | 'green'> = {
  0: 'green',
  37: 'green', // 00
  1: 'red', 3: 'red', 5: 'red', 7: 'red', 9: 'red',
  12: 'red', 14: 'red', 16: 'red', 18: 'red',
  19: 'red', 21: 'red', 23: 'red', 25: 'red', 27: 'red',
  30: 'red', 32: 'red', 34: 'red', 36: 'red',
  2: 'black', 4: 'black', 6: 'black', 8: 'black', 10: 'black',
  11: 'black', 13: 'black', 15: 'black', 17: 'black',
  20: 'black', 22: 'black', 24: 'black', 26: 'black', 28: 'black',
  29: 'black', 31: 'black', 33: 'black', 35: 'black'
};

export const ROULETTE_PAYOUTS: Record<RouletteBetType, number> = {
  single: 35,
  red: 1,
  black: 1,
  even: 1,
  odd: 1,
  low: 1,
  high: 1,
  first_dozen: 2,
  second_dozen: 2,
  third_dozen: 2,
  first_column: 2,
  second_column: 2,
  third_column: 2
};

// Static odds lookup for roulette bet types (used for potential win display)
export const ROULETTE_BET_ODDS: Record<string, number> = {
  // Single numbers (35:1 payout)
  '0': 36, '00': 36,
  '1': 36, '2': 36, '3': 36, '4': 36, '5': 36, '6': 36, '7': 36, '8': 36, '9': 36,
  '10': 36, '11': 36, '12': 36, '13': 36, '14': 36, '15': 36, '16': 36, '17': 36,
  '18': 36, '19': 36, '20': 36, '21': 36, '22': 36, '23': 36, '24': 36,
  '25': 36, '26': 36, '27': 36, '28': 36, '29': 36, '30': 36, '31': 36, '32': 36,
  '33': 36, '34': 36, '35': 36, '36': 36,
  // Even money bets (1:1 payout)
  'red': 2, 'black': 2, 'even': 2, 'odd': 2, '1-18': 2, '19-36': 2,
  // Dozens (2:1 payout)
  '1st12': 3, '2nd12': 3, '3rd12': 3,
  // Columns (2:1 payout)
  'col1': 3, 'col2': 3, 'col3': 3,
};

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
}
