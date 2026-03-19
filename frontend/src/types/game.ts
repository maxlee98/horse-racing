export type GameStatus = 'waiting' | 'open' | 'locked' | 'ended';
export type GameMode = 'standard' | 'horse_racing';

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
  | 'race_ended';

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
}
