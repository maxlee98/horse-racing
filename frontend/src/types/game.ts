export type GameStatus = 'waiting' | 'open' | 'locked' | 'ended';

export interface BetOption {
  id: string;
  label: string;
  odds: number;
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
  | 'error';

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
}
