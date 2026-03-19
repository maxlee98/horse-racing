'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useWebSocket } from '@/hooks/useWebSocket';
import { RoomState, WSMessage, RaceState, RacePosition, RaceResults } from '@/types/game';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function HostPage() {
  const { roomId } = useParams<{ roomId: string }>();
  const [hostId, setHostId] = useState('');
  const [room, setRoom] = useState<RoomState | null>(null);
  const [qr, setQr] = useState<{ qr_base64: string; join_url: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [showProbabilities, setShowProbabilities] = useState(false);
  const [editingProbs, setEditingProbs] = useState<Record<string, number>>({});
  const [raceState, setRaceState] = useState<RaceState>({
    is_racing: false,
    positions: [],
    progress: 0,
    winner_id: null,
  });
  const [raceResults, setRaceResults] = useState<RaceResults | null>(null);

  useEffect(() => {
    const id = sessionStorage.getItem(`host_${roomId}`);
    if (id) setHostId(id);
  }, [roomId]);

  const handleMessage = useCallback((msg: WSMessage) => {
    const state = (msg.data as Record<string, RoomState>).room_state;
    
    if (msg.type === 'room_state') {
      const rs = msg.data as unknown as RoomState;
      setRoom(rs);
      const probs: Record<string, number> = {};
      rs.bet_options.forEach(opt => {
        probs[opt.id] = Math.round((opt.probability || 0) * 100);
      });
      setEditingProbs(probs);
    } else if (state) {
      setRoom(state);
      const probs: Record<string, number> = {};
      state.bet_options.forEach(opt => {
        probs[opt.id] = Math.round((opt.probability || 0) * 100);
      });
      setEditingProbs(probs);
    }

    if (msg.type === 'race_started') {
      const horses = (msg.data as { horses: Array<{ id: string; label: string; probability: number }> }).horses;
      setRaceState({
        is_racing: true,
        positions: horses.map(h => ({ option_id: h.id, label: h.label, position: 0, probability: h.probability })),
        progress: 0,
        winner_id: null,
      });
      setRaceResults(null);
    } else if (msg.type === 'race_progress') {
      const data = msg.data as { positions: RacePosition[]; progress: number; race_complete?: boolean; finished_count?: number };
      setRaceState(prev => ({ 
        ...prev, 
        positions: data.positions, 
        progress: data.progress,
        finished_count: data.finished_count 
      }));
    } else if (msg.type === 'race_ended') {
      const data = msg.data as { winner_id: string; final_results?: RacePosition[]; race_duration?: number };
      setRaceState(prev => ({ ...prev, is_racing: false, winner_id: data.winner_id }));
      if (data.final_results && data.race_duration) {
        const winner = data.final_results.find(p => p.is_winner);
        setRaceResults({
          positions: data.final_results,
          race_duration: data.race_duration,
          winner_id: data.winner_id,
          winner_label: winner?.label || 'Unknown'
        });
      }
    }
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
      .then(r => r.json()).then((data) => {
        setRoom(data);
        const probs: Record<string, number> = {};
        data.bet_options.forEach((opt: { id: string; probability: number }) => {
          probs[opt.id] = Math.round((opt.probability || 0) * 100);
        });
        setEditingProbs(probs);
      }).catch(() => {});
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

  const updateProbabilities = () => {
    const probs: Record<string, number> = {};
    Object.entries(editingProbs).forEach(([id, val]) => {
      probs[id] = Math.max(0, Math.min(100, val)) / 100;
    });
    hostAction('update_probabilities', { probabilities: probs });
  };

  const randomizeProbabilities = () => {
    hostAction('randomize_probabilities');
  };

  const handleProbChange = (optionId: string, value: number) => {
    setEditingProbs(prev => ({ ...prev, [optionId]: Math.max(0, Math.min(100, value)) }));
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
              {room?.game_mode === 'horse_racing' && (
                <span className="text-lg" title="Horse Racing Mode">🏇</span>
              )}
            </div>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Room: <span className="font-mono font-bold" style={{ color: 'var(--accent-glow)' }}>{roomId}</span>
              &nbsp;·&nbsp;
              <span className={connected ? 'text-green-400' : 'text-red-400'}>
                {connected ? '● Connected' : '○ Disconnected'}
              </span>
              {room && <>&nbsp;·&nbsp;Round {room.round_number}</>}
            </p>
          </div>
        </div>

        {/* Horse Racing Animation Overlay */}
        {raceState.is_racing && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.95)' }}>
            <div className="w-full max-w-4xl">
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
                  <h2 className="text-3xl font-black text-center mb-8">🏇 The Race is On! 🏇</h2>
                  <div className="space-y-4">
                    {raceState.positions.map((pos) => {
                      const isWinner = pos.is_winner;
                      const rank = pos.rank || 0;
                      const rankDisplay = rank > 0 ? `${rank}${rank === 1 ? 'st' : rank === 2 ? 'nd' : rank === 3 ? 'rd' : 'th'}` : '-';
                      const hasFinished = pos.finish_time !== undefined && pos.finish_time !== null;
                      
                      return (
                        <div key={pos.option_id}>
                          <div className="flex items-center gap-3 mb-1">
                            <span className="text-lg">{isWinner ? '🏆' : '🐎'}</span>
                            <span className={`text-sm font-medium w-32 truncate ${isWinner ? 'font-black text-green-400' : ''}`}>
                              {pos.label}
                            </span>
                            <span className="text-xs px-2 py-0.5 rounded" style={{ 
                              background: rank === 1 ? 'rgba(34, 197, 94, 0.2)' : rank === 2 ? 'rgba(234, 179, 8, 0.2)' : rank === 3 ? 'rgba(249, 115, 22, 0.2)' : 'var(--bg-elevated)',
                              color: rank === 1 ? '#4ade80' : rank === 2 ? '#facc15' : rank === 3 ? '#fb923c' : 'var(--text-muted)',
                              border: `1px solid ${rank === 1 ? '#22c55e' : rank === 2 ? '#eab308' : rank === 3 ? '#f97316' : 'var(--border)'}`,
                              fontWeight: 'bold'
                            }}>
                              {rankDisplay}
                            </span>
                            {hasFinished && (
                              <span className="text-xs" style={{ color: '#4ade80' }}>
                                {pos.finish_time?.toFixed(2)}s
                              </span>
                            )}
                          </div>
                          <div className="h-8 rounded-full overflow-hidden" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                            <div 
                              className="h-full transition-all duration-100 flex items-center justify-end pr-2"
                              style={{ 
                                width: `${Math.min(pos.position, 100)}%`, 
                                background: isWinner 
                                  ? 'linear-gradient(90deg, #22c55e 0%, #4ade80 100%)' 
                                  : 'linear-gradient(90deg, var(--accent) 0%, var(--accent-glow) 100%)' 
                              }}>
                              <span className="text-lg">{isWinner ? '🏆' : '🐎'}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-6 text-center">
                    <div className="inline-block px-4 py-2 rounded-lg" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                      <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                        {(raceState as { finished_count?: number }).finished_count !== undefined 
                          ? `${(raceState as { finished_count?: number }).finished_count}/${raceState.positions.length} Finished`
                          : `Race Progress: ${Math.round(raceState.progress * 100)}%`
                        }
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-4">
            <div className="card p-5 text-center">
              <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>Scan to Join</p>
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
            <div className="card p-5 space-y-3">
              <StatRow label="Players" value={`${connectedPlayers.length} / ${room?.max_players || 8}`} />
              <StatRow label="Total Bets" value={`$${totalBetAmount.toFixed(0)}`} />
              <StatRow label="Bets Placed" value={String(room?.bets.length || 0)} />
              <StatRow label="Round" value={String(room?.round_number || 1)} />
            </div>
          </div>

          <div className="space-y-4">
            <div className="card p-5">
              <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Game Controls</p>
              <div className="space-y-2">
                <ControlBtn onClick={() => hostAction('open_bets')} disabled={room?.status === 'open'} color="var(--green)">🎯 Open Betting</ControlBtn>
                <ControlBtn onClick={() => hostAction('lock_bets')} disabled={room?.status !== 'open'} color="var(--amber)">🔒 Lock Bets</ControlBtn>
                {room?.status === 'ended' && (
                  <ControlBtn onClick={() => hostAction('next_round')} color="var(--accent-glow)">➡️ Next Round (Randomize Probs)</ControlBtn>
                )}
                <ControlBtn onClick={() => hostAction('reset_lobby')} color="var(--red)">🔄 Reset Lobby</ControlBtn>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>Win Probabilities</p>
                <button onClick={() => setShowProbabilities(!showProbabilities)} className="text-xs px-2 py-1 rounded" style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)' }}>
                  {showProbabilities ? 'Hide' : 'Show'}
                </button>
              </div>
              {showProbabilities && (
                <>
                  <div className="space-y-3 mb-4">
                    {room?.bet_options.map(opt => (
                      <div key={opt.id} className="flex items-center gap-3">
                        <span className="text-sm flex-1 truncate">{opt.label}</span>
                        <div className="flex items-center gap-2">
                          <input type="number" min="0" max="100"
                            value={editingProbs[opt.id] ?? Math.round((opt.probability || 0) * 100)}
                            onChange={(e) => handleProbChange(opt.id, parseInt(e.target.value) || 0)}
                            className="w-16 px-2 py-1 rounded text-sm text-center"
                            style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }} />
                          <span className="text-sm" style={{ color: 'var(--text-muted)' }}>%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <button onClick={updateProbabilities} className="flex-1 py-2 rounded-lg text-sm font-medium" style={{ background: 'var(--accent-soft)', color: 'var(--accent-glow)', border: '1px solid var(--accent)' }}>💾 Save Probs</button>
                    <button onClick={randomizeProbabilities} className="flex-1 py-2 rounded-lg text-sm font-medium" style={{ background: 'var(--bg-elevated)', color: 'var(--text)', border: '1px solid var(--border)' }}>🎲 Randomize</button>
                  </div>
                  <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>Total: {Object.values(editingProbs).reduce((a, b) => a + (b || 0), 0)}%</p>
                </>
              )}
              {!showProbabilities && (
                <div className="space-y-2">
                  {room?.bet_options.map(opt => (
                    <div key={opt.id} className="flex items-center justify-between text-sm">
                      <span style={{ color: 'var(--text-muted)' }}>{opt.label}</span>
                      <span className="font-mono" style={{ color: 'var(--accent-glow)' }}>{Math.round((opt.probability || 0) * 100)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {room && room.status === 'locked' && room.game_mode !== 'horse_racing' && (
              <div className="card p-5">
                <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>Declare Winner</p>
                <div className="space-y-2">
                  {room.bet_options.map(opt => (
                    <button key={opt.id} onClick={() => hostAction('set_winner', { option_id: opt.id })}
                      className="w-full py-2.5 px-4 rounded-lg text-sm font-semibold text-left" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}>
                      🏆 {opt.label} <span style={{ color: 'var(--text-muted)' }}>×{opt.odds} ({Math.round((opt.probability || 0) * 100)}%)</span>
                    </button>
                  ))}
                </div>
                <button onClick={() => hostAction('select_winner_by_probability')} className="w-full mt-3 py-2.5 px-4 rounded-lg text-sm font-semibold" style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent)', color: 'var(--accent-glow)' }}>
                  🎲 Auto-Select by Probability
                </button>
              </div>
            )}

            {/* Race Results - replaces the winner box for horse racing */}
            {raceResults && room?.game_mode === 'horse_racing' && (
              <div className="card p-5" style={{ borderColor: 'var(--green)', background: 'rgba(34, 197, 94, 0.05)' }}>
                <h3 className="text-lg font-black text-center mb-3" style={{ color: 'var(--green)' }}>🏆 Race Results</h3>
                <div className="space-y-2">
                  {raceResults.positions?.map((pos) => {
                    const medal = pos.rank === 1 ? '🥇' : pos.rank === 2 ? '🥈' : pos.rank === 3 ? '🥉' : `${pos.rank}th`;
                    return (
                      <div key={pos.option_id} className="flex items-center justify-between p-2 rounded-lg" 
                        style={{ 
                          background: pos.is_winner ? 'rgba(34, 197, 94, 0.2)' : 'var(--bg-elevated)',
                          border: `1px solid ${pos.is_winner ? '#22c55e' : 'var(--border)'}`
                        }}>
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{medal}</span>
                          <span className={`font-medium ${pos.is_winner ? 'text-green-400 font-black' : ''}`}>
                            {pos.label}
                            {pos.is_winner && <span className="ml-2">(WINNER)</span>}
                          </span>
                        </div>
                        <span className="font-mono text-sm" style={{ color: '#4ade80' }}>
                          {pos.finish_time?.toFixed(2)}s
                        </span>
                      </div>
                    );
                  })}
                </div>
                <p className="text-center mt-3 text-xs" style={{ color: 'var(--text-muted)' }}>
                  Race Time: <span className="font-mono" style={{ color: 'var(--accent-glow)' }}>{raceResults.race_duration?.toFixed(2)}s</span>
                </p>
              </div>
            )}

            {/* Standard winner display for non-horse racing */}
            {room?.status === 'ended' && room.winner_option_id && room?.game_mode !== 'horse_racing' && (
              <div className="card p-5 text-center glow-green" style={{ borderColor: 'var(--green)' }}>
                <p className="text-2xl mb-1">🏆</p>
                <p className="font-black text-lg" style={{ color: 'var(--green)' }}>
                  {room.bet_options.find(o => o.id === room.winner_option_id)?.label} Wins!
                </p>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="card p-5">
              <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>Players</p>
              {connectedPlayers.length === 0 ? (
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Waiting for players to scan…</p>
              ) : (
                <div className="space-y-2">
                  {connectedPlayers.map(p => (
                    <div key={p.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold" style={{ background: 'var(--accent-soft)', color: 'var(--accent-glow)' }}>
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

            <div className="card p-5">
              <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>Bets Placed</p>
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
                      <span className="font-mono font-bold" style={{ color: statusColor(room?.status || '') }}>${b.amount}</span>
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

function ControlBtn({ onClick, disabled, color, children }: { onClick: () => void; disabled?: boolean; color: string; children: React.ReactNode }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className="w-full py-2.5 px-4 rounded-lg text-sm font-semibold transition-all"
      style={{ background: disabled ? 'rgba(255,255,255,0.03)' : `rgba(${color}, 0.1)`, color: disabled ? 'var(--text-muted)' : color, border: `1px solid ${disabled ? 'var(--border)' : color}`, cursor: disabled ? 'not-allowed' : 'pointer' }}>
      {children}
    </button>
  );
}
