'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useWebSocket } from '@/hooks/useWebSocket';
import { RoomState, WSMessage } from '@/types/game';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function HostPage() {
  const { roomId } = useParams<{ roomId: string }>();
  const [hostId, setHostId] = useState('');
  const [room, setRoom] = useState<RoomState | null>(null);
  const [qr, setQr] = useState<{ qr_base64: string; join_url: string } | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const id = sessionStorage.getItem(`host_${roomId}`);
    if (id) setHostId(id);
  }, [roomId]);

  const handleMessage = useCallback((msg: WSMessage) => {
    const state = (msg.data as Record<string, RoomState>).room_state;
    if (msg.type === 'room_state') setRoom(msg.data as unknown as RoomState);
    else if (state) setRoom(state);
  }, []);

  const { connected, send } = useWebSocket({
    roomId,
    clientId: hostId,
    onMessage: handleMessage,
  });

  useEffect(() => {
    if (!roomId) return;
    fetch(`${API}/api/rooms/${roomId}/qr?base_url=${window.location.origin}`)
      .then(r => r.json()).then(setQr).catch(() => {});
    fetch(`${API}/api/rooms/${roomId}`)
      .then(r => r.json()).then(setRoom).catch(() => {});
  }, [roomId]);

  const hostAction = (action: string, extra: Record<string, unknown> = {}) => {
    send('host_action', { action, ...extra });
  };

  const copyLink = () => {
    if (qr?.join_url) {
      navigator.clipboard.writeText(qr.join_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const connectedPlayers = room ? Object.values(room.players).filter(p => p.is_connected) : [];
  const totalBetAmount = room?.bets.reduce((sum, b) => sum + b.amount, 0) || 0;

  const statusColor = (s: string) => {
    if (s === 'open') return 'var(--green)';
    if (s === 'locked') return 'var(--amber)';
    if (s === 'ended') return 'var(--red)';
    return 'var(--text-muted)';
  };

  return (
    <main className="min-h-screen p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-black">{room?.title || 'Loading...'}</h1>
              {room && (
                <span className={`status-badge status-${room.status}`}>
                  {room.status === 'open' && <span className="live-dot" />}
                  {room.status}
                </span>
              )}
            </div>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Room: <span className="font-mono font-bold" style={{ color: 'var(--accent-glow)' }}>{roomId}</span>
              &nbsp;·&nbsp;
              <span className={connected ? 'text-green-400' : 'text-red-400'}>
                {connected ? '● Connected' : '○ Disconnected'}
              </span>
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left — QR + Stats */}
          <div className="space-y-4">
            {/* QR Card */}
            <div className="card p-5 text-center">
              <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
                Scan to Join
              </p>
              {qr ? (
                <img src={qr.qr_base64} alt="QR Code" className="w-44 h-44 mx-auto rounded-lg" />
              ) : (
                <div className="w-44 h-44 mx-auto rounded-lg flex items-center justify-center" style={{ background: 'var(--bg-elevated)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Loading QR…</span>
                </div>
              )}
              <button onClick={copyLink} className="mt-3 w-full py-2 rounded-lg text-sm font-medium transition-all"
                style={{ background: copied ? 'var(--green-soft)' : 'var(--accent-soft)', color: copied ? 'var(--green)' : 'var(--accent-glow)', border: `1px solid ${copied ? 'var(--green)' : 'var(--accent)'}` }}>
                {copied ? '✓ Copied!' : '🔗 Copy Link'}
              </button>
            </div>

            {/* Stats */}
            <div className="card p-5 space-y-3">
              <StatRow label="Players" value={`${connectedPlayers.length} / ${room?.max_players || 8}`} />
              <StatRow label="Total Bets" value={`$${totalBetAmount.toFixed(0)}`} />
              <StatRow label="Bets Placed" value={String(room?.bets.length || 0)} />
            </div>
          </div>

          {/* Middle — Controls */}
          <div className="space-y-4">
            <div className="card p-5">
              <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>
                Game Controls
              </p>
              <div className="space-y-2">
                <ControlBtn onClick={() => hostAction('open_bets')} disabled={room?.status === 'open'} color="var(--green)">
                  🎯 Open Betting
                </ControlBtn>
                <ControlBtn onClick={() => hostAction('lock_bets')} disabled={room?.status !== 'open'} color="var(--amber)">
                  🔒 Lock Bets
                </ControlBtn>
                <ControlBtn onClick={() => hostAction('reset')} color="var(--text-muted)">
                  🔄 Reset Round
                </ControlBtn>
              </div>
            </div>

            {/* Set Winner */}
            {room && room.status === 'locked' && (
              <div className="card p-5">
                <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
                  Declare Winner
                </p>
                <div className="space-y-2">
                  {room.bet_options.map(opt => (
                    <button key={opt.id}
                      onClick={() => hostAction('set_winner', { option_id: opt.id })}
                      className="w-full py-2.5 px-4 rounded-lg text-sm font-semibold text-left transition-all"
                      style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}
                      onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--green)')}
                      onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}>
                      🏆 {opt.label} <span style={{ color: 'var(--text-muted)' }}>×{opt.odds}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Winner display */}
            {room?.status === 'ended' && room.winner_option_id && (
              <div className="card p-5 text-center glow-green" style={{ borderColor: 'var(--green)' }}>
                <p className="text-2xl mb-1">🏆</p>
                <p className="font-black text-lg" style={{ color: 'var(--green)' }}>
                  {room.bet_options.find(o => o.id === room.winner_option_id)?.label} Wins!
                </p>
              </div>
            )}
          </div>

          {/* Right — Players + Bets */}
          <div className="space-y-4">
            {/* Players */}
            <div className="card p-5">
              <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
                Players
              </p>
              {connectedPlayers.length === 0 ? (
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Waiting for players to scan…</p>
              ) : (
                <div className="space-y-2">
                  {connectedPlayers.map(p => (
                    <div key={p.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                          style={{ background: 'var(--accent-soft)', color: 'var(--accent-glow)' }}>
                          {p.name[0]?.toUpperCase()}
                        </div>
                        <span className="text-sm font-medium">{p.name}</span>
                      </div>
                      <span className="text-sm font-mono" style={{ color: 'var(--green)' }}>${p.balance.toFixed(0)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Bets */}
            <div className="card p-5">
              <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
                Bets Placed
              </p>
              {room?.bets.length === 0 ? (
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No bets yet</p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {[...(room?.bets || [])].reverse().map((b, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <div>
                        <span className="font-medium">{b.player_name}</span>
                        <span style={{ color: 'var(--text-muted)' }}> → {b.option_label}</span>
                      </div>
                      <span className="font-mono font-bold" style={{ color: statusColor(room?.status || '') }}>
                        ${b.amount}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span className="text-sm font-bold">{value}</span>
    </div>
  );
}

function ControlBtn({ onClick, disabled, color, children }: {
  onClick: () => void; disabled?: boolean; color: string; children: React.ReactNode;
}) {
  return (
    <button onClick={onClick} disabled={disabled}
      className="w-full py-2.5 px-4 rounded-lg text-sm font-semibold transition-all"
      style={{ background: disabled ? 'rgba(255,255,255,0.03)' : `rgba(${color}, 0.1)`, color: disabled ? 'var(--text-muted)' : color, border: `1px solid ${disabled ? 'var(--border)' : color}`, cursor: disabled ? 'not-allowed' : 'pointer' }}>
      {children}
    </button>
  );
}
