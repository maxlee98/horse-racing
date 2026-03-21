/**
 * Shared constants across the application
 *
 * IMPORTANT: These should stay in sync with backend/core/constants.py
 * The frontend fetches the source of truth from /api/constants on app load
 * and stores in a global state or context.
 */

// Fallback constants (used before API fetch or if fetch fails)
export const FALLBACK_CONSTANTS = {
  roulette: {
    wheel_order: [
      0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1,
      37, // 00
      27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16, 4, 23, 35, 14, 2
    ],
    colors: {
      0: 'green',
      37: 'green',
      // Red numbers
      1: 'red', 3: 'red', 5: 'red', 7: 'red', 9: 'red',
      12: 'red', 14: 'red', 16: 'red', 18: 'red',
      19: 'red', 21: 'red', 23: 'red', 25: 'red', 27: 'red',
      30: 'red', 32: 'red', 34: 'red', 36: 'red',
      // Black numbers
      2: 'black', 4: 'black', 6: 'black', 8: 'black', 10: 'black',
      11: 'black', 13: 'black', 15: 'black', 17: 'black',
      20: 'black', 22: 'black', 24: 'black', 26: 'black', 28: 'black',
      29: 'black', 31: 'black', 33: 'black', 35: 'black'
    } as Record<number, 'red' | 'black' | 'green'>,
    payouts: {
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
      third_column: 2,
    } as Record<string, number>,
  },
  max_players: 8,
  default_balance: 1000,
  quick_bet_amounts: [50, 100, 200, 500],
} as const;

// Game mode presets (fallback)
export const GAME_PRESETS = {
  standard: {
    title: '',
    options: [
      { id: '1', label: 'Team A', odds: 1.8 },
      { id: '2', label: 'Team B', odds: 2.1 },
    ],
    useRandomizedProbabilities: false,
  },

  horseRacing: {
    title: '🏇 Horse Racing',
    options: [
      { id: '1', label: '🐎 Thunder Bolt', odds: 2.5 },
      { id: '2', label: '🐎 Midnight Runner', odds: 3.0 },
      { id: '3', label: '🐎 Golden Mane', odds: 2.0 },
      { id: '4', label: '🐎 Silver Streak', odds: 4.0 },
      { id: '5', label: '🐎 Wild Spirit', odds: 3.5 },
    ],
    useRandomizedProbabilities: true,
  },

  roulette: {
    title: '🎰 Roulette',
    options: [
      // Individual numbers (0, 00, 1-36)
      { id: '0', label: '0', odds: 36 },
      { id: '00', label: '00', odds: 36 },
      ...Array.from({ length: 36 }, (_, i) => ({
        id: String(i + 1),
        label: String(i + 1),
        odds: 36
      })),
      // Even money bets
      { id: 'red', label: 'Red', odds: 2 },
      { id: 'black', label: 'Black', odds: 2 },
      { id: 'even', label: 'Even', odds: 2 },
      { id: 'odd', label: 'Odd', odds: 2 },
      { id: '1-18', label: '1-18 (Low)', odds: 2 },
      { id: '19-36', label: '19-36 (High)', odds: 2 },
      // Dozens
      { id: '1st12', label: '1st 12', odds: 3 },
      { id: '2nd12', label: '2nd 12', odds: 3 },
      { id: '3rd12', label: '3rd 12', odds: 3 },
      // Columns
      { id: 'col1', label: 'Column 1', odds: 3 },
      { id: 'col2', label: 'Column 2', odds: 3 },
      { id: 'col3', label: 'Column 3', odds: 3 },
    ],
    useRandomizedProbabilities: false,
  },
} as const;

// Default amounts for quick bet buttons
export const QUICK_BET_AMOUNTS = [50, 100, 200, 500] as const;

// Max players per room
export const MAX_PLAYERS = 8;

// Default starting balance
export const DEFAULT_BALANCE = 1000;

// Status colors for UI
export const STATUS_COLORS = {
  waiting: 'var(--text-muted)',
  open: 'var(--green)',
  locked: 'var(--amber)',
  ended: 'var(--red)',
} as const;

// Roulette specific exports for convenience
export const ROULETTE_WHEEL_ORDER = FALLBACK_CONSTANTS.roulette.wheel_order;
export const ROULETTE_COLORS = FALLBACK_CONSTANTS.roulette.colors;
export const ROULETTE_PAYOUTS = FALLBACK_CONSTANTS.roulette.payouts;
