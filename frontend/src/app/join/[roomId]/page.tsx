'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useWebSocket } from '@/hooks/useWebSocket';
import { RoomState, WSMessage, Bet, RaceState, RacePosition, RouletteState, RouletteBetType, ROULETTE_BET_ODDS } from '@/types/game';
import RouletteWheel from '@/components/RouletteWheel';
import RouletteTable from '@/components/RouletteTable';

export default function JoinPage() {
  const { roomId } = useParams<{ roomId: string }>();
  const [playerId] = useState(() => {
    if (typeof window !== 'undefined') {
      const existing = sessionStorage.getItem(`player_${roomId}`);
      if (existing) return existing;
      const id = crypto.randomUUID();
      sessionStorage.setItem(`player_${roomId}`, id);
      return id;
    }
    return crypto.randomUUID();
  });
  const [name, setName] = useState('');
  const [joined, setJoined] = useState(false);
  const [room, setRoom] = useState<RoomState | null>(null);
  const [selectedOption, setSelectedOption] = useState('');
  const [betAmount, setBetAmount] = useState('100');
  const [myBets, setMyBets] = useState<Bet[]>([]);
  const [notification, setNotification] = useState('');
  const [raceState, setRaceState] = useState<RaceState>({
    is_racing: false,
    positions: [],
    progress: 0,
    winner_id: null,
  });
  const [rouletteState, setRouletteState] = useState<RouletteState>({
    is_spinning: false,
    wheel_rotation: 0,
    ball_position: 0,
    ball_radius: 100,
    winning_number: null,
    winning_color: null,
    phase: null,
    progress: 0,
  });
  const [selectedBetType, setSelectedBetType] = useState<RouletteBetType | null>(null);
  const [selectedNumber, setSelectedNumber] = useState<number | undefined>(undefined);
  const [gameResults, setGameResults] = useState<{
    winningNumber: string;
    winningColor: string;
    myBets: Array<{ label: string; amount: number; won: boolean; payout: number }>;
    totalBet: number;
    totalWon: number;
    netResult: number;
  } | null>(null);
  const notifTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const notify = (msg: string) => {
    setNotification(msg);
    if (notifTimeout.current) clearTimeout(notifTimeout.current);
    notifTimeout.current = setTimeout(() => setNotification(''), 3000);
  };

  const handleMessage = useCallback((msg: WSMessage) => {
    const state = (msg.data as Record<string, RoomState>).room_state;
    if (msg.type === 'room_state') {
      const rs = msg.data as unknown as RoomState;
      setRoom(rs);
      setMyBets(rs.bets.filter(b => b.player_id === playerId));
    } else if (state) {
      setRoom(state);
      setMyBets(state.bets.filter(b => b.player_id === playerId));
    }
    if (msg.type === 'bet_placed') {
      const bet = (msg.data as { bet: Bet }).bet;
      if (bet.player_id === playerId) notify(`✅ Bet placed: $${bet.amount} on ${bet.option_label}`);
      else notify(`📢 ${bet.player_name} bet $${bet.amount} on ${bet.option_label}`);
    }
    if (msg.type === 'game_updated') {
      const s = (msg.data as { room_state: RoomState }).room_state;
      if (s.status === 'open') notify('🎯 Bets are now open!');
      if (s.status === 'locked') notify('🔒 Bets are locked!');
      if (s.status === 'ended') notify('🏁 Game ended!');
    }
    if (msg.type === 'game_ended') {
      const data = msg.data as { winner_option_id: string; winning_bets: Array<{ player_id: string; payout: number; option_label?: string }> };
      const myWinningBets = data.winning_bets.filter(wb => wb.player_id === playerId);
      if (myWinningBets.length > 0) {
        const totalPayout = myWinningBets.reduce((sum, wb) => sum + wb.payout, 0);
        notify(`🏆 You won $${totalPayout.toFixed(2)}!`);
      }
    }
    if (msg.type === 'error') {
      notify(`❌ ${(msg.data as { message: string }).message}`);
    }

    // Handle horse racing messages
    if (msg.type === 'race_started') {
      const horses = (msg.data as { horses: Array<{ id: string; label: string; probability: number }> }).horses;
      setRaceState({
        is_racing: true,
        positions: horses.map(h => ({ option_id: h.id, label: h.label, position: 0, probability: h.probability })),
        progress: 0,
        winner_id: null,
      });
    } else if (msg.type === 'race_progress') {
      const { positions, progress, countdown, message } = msg.data as { 
        positions: RacePosition[]; 
        progress: number;
        countdown?: number;
        message?: string;
      };
      setRaceState(prev => ({
        ...prev,
        positions,
        progress,
        countdown,
        message,
      }));
    } else if (msg.type === 'race_ended') {
      const { winner_id, winner_label } = msg.data as { winner_id: string; winner_label: string };
      setRaceState(prev => ({
        ...prev,
        is_racing: false,
        winner_id,
      }));
      notify(`🏆 ${winner_label} won the race!`);
    }

    // Handle roulette messages
    if (msg.type === 'roulette_started') {
      setRouletteState({
        is_spinning: true,
        wheel_rotation: 0,
        ball_position: 0,
        ball_radius: 100,
        winning_number: null,
        winning_color: null,
        phase: 'accelerating',
        progress: 0,
      });
    } else if (msg.type === 'roulette_progress' || msg.type === 'roulette_ball_settling') {
      const data = msg.data as {
        wheel_rotation: number;
        ball_position: number;
        ball_radius: number;
        phase: string;
        progress: number;
        countdown?: number;
        message?: string;
      };
      setRouletteState(prev => ({
        ...prev,
        wheel_rotation: data.wheel_rotation,
        ball_position: data.ball_position,
        ball_radius: data.ball_radius,
        phase: data.phase as RouletteState['phase'],
        progress: data.progress,
        countdown: data.countdown,
        message: data.message,
      }));
    } else if (msg.type === 'roulette_ended') {
      const data = msg.data as {
        winning_number: string;
        winning_number_int: number;
        winning_color: string;
        winning_bets?: Array<{ player_id: string; option_id: string; option_label: string; amount: number; payout: number }>;
        room_state?: RoomState;
      };
      
      // Update room state so the results module renders with status='ended'
      if (data.room_state) {
        setRoom(data.room_state);
        setMyBets(data.room_state.bets.filter(b => b.player_id === playerId));
      }
      
      setRouletteState(prev => ({
        ...prev,
        is_spinning: false,
        winning_number: data.winning_number,
        winning_color: data.winning_color as 'red' | 'black' | 'green',
        phase: 'revealing',
        progress: 1,
      }));
      notify(`🎰 ${data.winning_number} ${data.winning_color} wins!`);
      
      // Calculate game results for display
      const myWinningBets = data.winning_bets?.filter(wb => wb.player_id === playerId) || [];
      
      setGameResults(prev => {
        const currentMyBets = myBets;
        const totalBet = currentMyBets.reduce((sum, b) => sum + b.amount, 0);
        const totalWon = myWinningBets.reduce((sum, wb) => sum + wb.payout, 0);
        
        return {
          winningNumber: data.winning_number,
          winningColor: data.winning_color,
          myBets: currentMyBets.map(bet => {
            const winningBet = myWinningBets.find(wb => wb.option_id === bet.option_id);
            return {
              label: bet.option_label,
              amount: bet.amount,
              won: !!winningBet,
              payout: winningBet?.payout || 0,
            };
          }),
          totalBet,
          totalWon,
          netResult: totalWon - totalBet,
        };
      });
    }

    // Handle game mode changed
    if (msg.type === 'game_mode_changed') {
      const data = msg.data as {
        new_game_mode: 'standard' | 'horse_racing' | 'roulette';
        room_state: RoomState;
        message?: string;
      };
      
      // Update room state
      setRoom(data.room_state);
      setMyBets(data.room_state.bets.filter(b => b.player_id === playerId));
      
      // Reset game-specific state
      setRaceState({ is_racing: false, positions: [], progress: 0, winner_id: null });
      setRouletteState({ 
        is_spinning: false, 
        wheel_rotation: 0, 
        ball_position: 0, 
        ball_radius: 100, 
        winning_number: null, 
        winning_color: null, 
        phase: null, 
        progress: 0 
      });
      setGameResults(null);
      setSelectedOption('');
      setSelectedBetType(null);
      setSelectedNumber(undefined);
      
      // Notify player
      notify(data.message || `🎮 Game changed to ${data.new_game_mode}!`);
    }
  }, [playerId, myBets]);

  const { connected, send } = useWebSocket({ roomId, clientId: playerId, onMessage: handleMessage });

  const joinGame = () => {
    if (!name.trim()) return;
    send('join', { name: name.trim() });
    setJoined(true);
  };

  const placeBet = () => {
    if (!selectedOption) { notify('Select an option first'); return; }
    const amt = parseFloat(betAmount);
    if (isNaN(amt) || amt <= 0) { notify('Enter a valid amount'); return; }
    send('place_bet', { 
      option_id: selectedOption, 
      amount: amt,
      bet_type: selectedBetType,
      bet_number: selectedNumber
    });
  };

  const me = room?.players[playerId];
  const winnerOption = room?.winner_option_id ? room.bet_options.find(o => o.id === room.winner_option_id) : null;
  const myWinnerBet = winnerOption ? myBets.find(b => b.option_id === winnerOption.id) : null;

  // Entry screen
  if (!joined) {
    return (
      <main className="min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="text-5xl mb-3">🎲</div>
            <h1 className="text-3xl font-black mb-1">Join Game</h1>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Room <span className="font-mono font-bold" style={{ color: 'var(--accent-glow)' }}>{roomId}</span></p>
          </div>
          <div className="card p-6 space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: 'var(--text-muted)' }}>
                Your Name
              </label>
              <input
                className="w-full px-4 py-3 rounded-lg text-sm outline-none"
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}
                placeholder="Enter your name..."
                value={name}
                onChange={e => setName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && joinGame()}
                autoFocus
              />
            </div>
            <button onClick={joinGame} disabled={!name.trim() || !connected} className="btn-primary w-full py-3 glow-accent">
              {connected ? '→ Enter Game' : 'Connecting...'}
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-4 pb-32">
      <div className="max-w-md mx-auto">
        {/* Notification */}
        {notification && (
          <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl text-sm font-medium shadow-xl"
            style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
            {notification}
          </div>
        )}

        {/* Horse Racing Animation Overlay */}
        {raceState.is_racing && (
          <div className="fixed inset-0 z-40 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.95)' }}>
            <div className="w-full max-w-md">
              {/* Countdown Display */}
              {raceState.countdown ? (
                <div className="text-center">
                  <div className="text-8xl font-black mb-4" style={{ color: 'var(--accent-glow)' }}>
                    {raceState.countdown}
                  </div>
                  <p className="text-xl" style={{ color: 'var(--text-muted)' }}>
                    {raceState.message}
                  </p>
                </div>
              ) : (
                <>
                  <h2 className="text-2xl font-black text-center mb-6">🏇 The Race is On! 🏇</h2>
                  <div className="space-y-3">
                    {raceState.positions.map((pos, index) => {
                      const isWinner = pos.is_winner;
                      const rank = pos.rank || (index + 1);
                      const rankSuffix = rank === 1 ? 'st' : rank === 2 ? 'nd' : rank === 3 ? 'rd' : 'th';
                      const momentum = pos.momentum ?? 0;
                      const momentumIcon = pos.momentum_surge ? '⚡' : momentum > 0.05 ? '🔥' : momentum < -0.05 ? '💨' : '';
                      
                      return (
                        <div key={pos.option_id}>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg">{isWinner ? '🏆' : '🐎'}</span>
                            <span className={`text-sm font-medium flex-1 truncate ${isWinner ? 'font-black text-green-400' : ''}`}>
                              {pos.label}
                              {isWinner && <span className="ml-2 text-green-400 font-black">WINNER!</span>}
                            </span>
                            {momentumIcon && (
                              <span className={`text-sm animate-pulse ${momentum > 0 ? 'text-orange-400' : 'text-blue-300'}`}>
                                {momentumIcon}
                              </span>
                            )}
                            <span className="text-xs" style={{ color: isWinner ? '#4ade80' : 'var(--text-muted)' }}>
                              {pos.position.toFixed(2)}% | {rank}{rankSuffix} | ×{room?.bet_options.find(o => o.id === pos.option_id)?.odds.toFixed(1)}
                            </span>
                          </div>
                          <div className="h-6 rounded-full overflow-hidden" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                            <div 
                              className="h-full transition-all duration-150 flex items-center justify-end pr-1"
                              style={{ 
                                width: `${Math.min(pos.position, 100)}%`, 
                                background: isWinner 
                                  ? 'linear-gradient(90deg, #22c55e 0%, #4ade80 100%)' 
                                  : 'linear-gradient(90deg, var(--accent) 0%, var(--accent-glow) 100%)' 
                              }}
                            >
                              <span>{isWinner ? '🏆' : '🐎'}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-4 text-center">
                    <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                      Race Progress: {Math.round(raceState.progress * 100)}%
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black truncate">{room?.title || '...'}</h1>
              {room?.game_mode === 'horse_racing' && <span>🏇</span>}
              {room?.game_mode === 'roulette' && <span>🎰</span>}
            </div>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {room ? `${room.player_count} players connected` : 'Loading...'}
            </p>
          </div>
          <div className="text-right">
            <span className={`status-badge status-${room?.status || 'waiting'}`}>
              {room?.status === 'open' && <span className="live-dot" />}
              {room?.status || '...'}
            </span>
            {me && <p className="text-xs mt-1 font-mono font-bold" style={{ color: 'var(--green)' }}>${me.balance.toFixed(0)}</p>}
          </div>
        </div>

        {/* Result banner */}
        {room?.status === 'ended' && winnerOption && room?.game_mode !== 'roulette' && (
          <div className="card p-4 mb-4 text-center" style={{ borderColor: myWinnerBet ? 'var(--green)' : 'var(--red)', background: myWinnerBet ? 'var(--green-soft)' : 'var(--red-soft)' }}>
            <p className="text-2xl mb-1">{myWinnerBet ? '🏆' : '💸'}</p>
            <p className="font-black text-lg">{winnerOption.label} won!</p>
            {myWinnerBet
              ? <p style={{ color: 'var(--green)' }}>You won <strong>+${myWinnerBet.potential_win}</strong>!</p>
              : <p style={{ color: 'var(--red)' }}>Better luck next time.</p>
            }
          </div>
        )}

        {/* Roulette Results Module */}
        {room?.status === 'ended' && room?.game_mode === 'roulette' && gameResults && (
          <div className="card p-4 mb-4" style={{ borderColor: gameResults.netResult >= 0 ? 'var(--green)' : 'var(--red)', background: gameResults.netResult >= 0 ? 'var(--green-soft)' : 'var(--red-soft)' }}>
            <div className="text-center mb-4">
              <p className="text-3xl mb-2">🎰</p>
              <p className="font-black text-lg">{gameResults.winningNumber} <span style={{ 
                color: gameResults.winningColor === 'red' ? '#DC2626' : gameResults.winningColor === 'black' ? '#1F2937' : '#059669',
                textTransform: 'uppercase'
              }}>{gameResults.winningColor}</span></p>
            </div>
            
            <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: 'var(--text-muted)' }}>Your Bets</p>
            <div className="space-y-2 mb-4">
              {gameResults.myBets.map((bet, i) => (
                <div key={i} className="flex items-center justify-between text-sm p-2 rounded" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <div className="flex items-center gap-2">
                    <span>{bet.won ? '✅' : '❌'}</span>
                    <span>{bet.label}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono">${bet.amount}</span>
                    {bet.won && (
                      <span className="ml-2 font-mono font-bold" style={{ color: 'var(--green)' }}>+${bet.payout.toFixed(2)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="border-t pt-3" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span style={{ color: 'var(--text-muted)' }}>Total Bet:</span>
                <span className="font-mono">${gameResults.totalBet.toFixed(2)}</span>
              </div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span style={{ color: 'var(--text-muted)' }}>Total Won:</span>
                <span className="font-mono" style={{ color: 'var(--green)' }}>${gameResults.totalWon.toFixed(2)}</span>
              </div>
              <div className="flex items-center justify-between text-lg font-bold mt-2 pt-2" style={{ borderTop: '1px solid var(--border)' }}>
                <span>Net Result:</span>
                <span style={{ color: gameResults.netResult >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  {gameResults.netResult >= 0 ? '+' : ''}${gameResults.netResult.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Bet Options - Roulette */}
        {room?.status !== 'ended' && room?.game_mode === 'roulette' && (
          <div className="mb-5">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
              {room?.status === 'waiting' ? 'Waiting for host to open betting...' : 'Choose Your Bet'}
            </p>
            {room?.status === 'waiting' ? (
              <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
                <div className="text-4xl mb-2">⏳</div>
                <p>Please wait for the host to open betting</p>
              </div>
            ) : (
              <RouletteTable
                selectedOption={selectedOption}
                onSelectOption={(optionId, betType, betNumber) => {
                  setSelectedOption(optionId);
                  setSelectedBetType(betType);
                  setSelectedNumber(betNumber);
                }}
                disabled={room.status !== 'open'}
                betOptions={room.bet_options}
                rouletteHistory={room.roulette_history || []}
              />
            )}
          </div>
        )}

        {/* Standard Bet Options (non-roulette) */}
        {room?.status !== 'ended' && room?.game_mode !== 'roulette' && (
          <div className="space-y-3 mb-5">
            <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>Choose Your Bet</p>
            {room?.bet_options.map(opt => {
              const isSelected = selectedOption === opt.id;
              const alreadyBet = myBets.some(b => b.option_id === opt.id);
              const totalOnOption = room.bets.filter(b => b.option_id === opt.id).reduce((s, b) => s + b.amount, 0);
              return (
                <button key={opt.id} onClick={() => !alreadyBet && room.status === 'open' && setSelectedOption(opt.id)}
                  disabled={alreadyBet || room.status !== 'open'}
                  className="w-full p-4 rounded-xl text-left transition-all"
                  style={{
                    background: isSelected ? 'var(--accent-soft)' : 'var(--bg-card)',
                    border: `2px solid ${isSelected ? 'var(--accent)' : alreadyBet ? 'var(--green)' : 'var(--border)'}`,
                    cursor: alreadyBet || room.status !== 'open' ? 'default' : 'pointer'
                  }}>
                  <div className="flex items-center justify-between">
                    <span className="font-bold">{opt.label}</span>
                    <div className="text-right">
                      <span className="text-lg font-black" style={{ color: 'var(--accent-glow)' }}>×{opt.odds}</span>
                      {alreadyBet && <span className="ml-2 text-xs px-2 py-0.5 rounded-full" style={{ background: 'var(--green-soft)', color: 'var(--green)' }}>✓ Bet</span>}
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Win chance: {Math.round((opt.probability || 0) * 100)}%</span>
                    <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>${totalOnOption.toFixed(0)} pooled</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Bet input */}
        {room?.status === 'open' && selectedOption && (
          <div className="card p-4 mb-5">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
              Bet Amount
            </p>
            <div className="flex gap-2 mb-3">
              {[50, 100, 200, 500].map(amt => (
                <button key={amt} onClick={() => setBetAmount(String(amt))}
                  className="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                  style={{ background: betAmount === String(amt) ? 'var(--accent-soft)' : 'var(--bg-elevated)', border: `1px solid ${betAmount === String(amt) ? 'var(--accent)' : 'var(--border)'}`, color: betAmount === String(amt) ? 'var(--accent-glow)' : 'var(--text-muted)' }}>
                  ${amt}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input 
                type="number" 
                className="flex-1 px-3 py-2.5 rounded-lg text-sm outline-none"
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}
                value={betAmount} 
                onChange={e => setBetAmount(e.target.value)} 
                placeholder="Custom amount" 
              />
              <button onClick={placeBet} className="btn-primary px-6 glow-accent">Place Bet</button>
            </div>
            {selectedOption && me && (
              <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                Potential win: <span className="font-bold" style={{ color: 'var(--green)' }}>
                  ${(parseFloat(betAmount || '0') * (room.game_mode === 'roulette' 
                    ? (ROULETTE_BET_ODDS[selectedOption] || ROULETTE_BET_ODDS[room.bet_options.find(o => o.id === selectedOption)?.label || ''] || 1)
                    : (room.bet_options.find(o => o.id === selectedOption)?.odds || 1)
                  )).toFixed(2)}
                </span>
              </p>
            )}
          </div>
        )}

        {/* Status messages */}
        {room?.status === 'waiting' && room?.game_mode !== 'roulette' && (
          <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
            <div className="text-4xl mb-2">⏳</div>
            <p>Waiting for host to open bets...</p>
          </div>
        )}
        {room?.status === 'locked' && room?.game_mode !== 'horse_racing' && (
          <div className="text-center py-8" style={{ color: 'var(--amber)' }}>
            <div className="text-4xl mb-2">🔒</div>
            <p className="font-bold">Bets are locked!</p>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Waiting for the result...</p>
          </div>
        )}
        {room?.status === 'locked' && room?.game_mode === 'horse_racing' && !raceState.is_racing && (
          <div className="text-center py-8" style={{ color: 'var(--amber)' }}>
            <div className="text-4xl mb-2">🏇</div>
            <p className="font-bold">Get ready!</p>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>The race is about to start...</p>
          </div>
        )}

        {/* My Bets */}
        {myBets.length > 0 && room?.status !== 'ended' && (
          <div className="card p-4">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>My Bets</p>
            <div className="space-y-2">
              {myBets.map((b, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span style={{ color: 'var(--text-muted)' }}>{b.option_label}</span>
                  <div className="text-right">
                    <span className="font-mono">${b.amount}</span>
                    <span style={{ color: 'var(--text-muted)' }}> → </span>
                    <span className="font-mono font-bold" style={{ color: 'var(--green)' }}>${b.potential_win}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
