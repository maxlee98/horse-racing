'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useWebSocket } from '@/hooks/useWebSocket';
import { RoomState, WSMessage, Bet } from '@/types/game';

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
    if (msg.type === 'error') {
      notify(`❌ ${(msg.data as { message: string }).message}`);
    }
  }, [playerId]);

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
    send('place_bet', { option_id: selectedOption, amount: amt });
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

        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-lg font-black truncate">{room?.title || '...'}</h1>
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
        {room?.status === 'ended' && winnerOption && (
          <div className="card p-4 mb-4 text-center" style={{ borderColor: myWinnerBet ? 'var(--green)' : 'var(--red)', background: myWinnerBet ? 'var(--green-soft)' : 'var(--red-soft)' }}>
            <p className="text-2xl mb-1">{myWinnerBet ? '🏆' : '💸'}</p>
            <p className="font-black text-lg">{winnerOption.label} won!</p>
            {myWinnerBet
              ? <p style={{ color: 'var(--green)' }}>You won <strong>+${myWinnerBet.potential_win}</strong>!</p>
              : <p style={{ color: 'var(--red)' }}>Better luck next time.</p>
            }
          </div>
        )}

        {/* Bet Options */}
        {room?.status !== 'ended' && (
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
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Total pooled</span>
                    <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>${totalOnOption.toFixed(0)}</span>
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
              <input type="number" className="flex-1 px-3 py-2.5 rounded-lg text-sm outline-none"
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}
                value={betAmount} onChange={e => setBetAmount(e.target.value)} placeholder="Custom amount" />
              <button onClick={placeBet} className="btn-primary px-6 glow-accent">Place Bet</button>
            </div>
            {selectedOption && me && (
              <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                Potential win: <span className="font-bold" style={{ color: 'var(--green)' }}>
                  ${(parseFloat(betAmount || '0') * (room.bet_options.find(o => o.id === selectedOption)?.odds || 1)).toFixed(2)}
                </span>
              </p>
            )}
          </div>
        )}

        {/* Status messages */}
        {room?.status === 'waiting' && (
          <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
            <div className="text-4xl mb-2">⏳</div>
            <p>Waiting for host to open bets...</p>
          </div>
        )}
        {room?.status === 'locked' && (
          <div className="text-center py-8" style={{ color: 'var(--amber)' }}>
            <div className="text-4xl mb-2">🔒</div>
            <p className="font-bold">Bets are locked!</p>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Waiting for the result...</p>
          </div>
        )}

        {/* My Bets */}
        {myBets.length > 0 && (
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
