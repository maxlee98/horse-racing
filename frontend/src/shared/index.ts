/**
 * Shared module exports
 * Import from '@/shared' for common utilities, types, and hooks
 */

// Types
export * from './types/game';

// Hooks
export { useWebSocket } from './hooks/useWebSocket';

// API
export { api } from './lib/api';

// Constants
export { GAME_PRESETS, QUICK_BET_AMOUNTS, MAX_PLAYERS, STATUS_COLORS } from './lib/constants';
