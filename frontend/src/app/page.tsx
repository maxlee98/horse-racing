'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface BetOptionInput {
  id: string;
  label: string;
  odds: number;
}

export default function HomePage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [options, setOptions] = useState<BetOptionInput[]>([
    { id: '1', label: 'Team A', odds: 1.8 },
    { id: '2', label: 'Team B', odds: 2.1 },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addOption = () => {
    setOptions([...options, { id: String(Date.now()), label: '', odds: 2.0 }]);
  };

  const removeOption = (index: number) => {
    setOptions(options.filter((_, i) => i !== index));
  };

  const updateOption = (index: number, field: keyof BetOptionInput, value: string | number) => {
    const updated = [...options];
    updated[index] = { ...updated[index], [field]: value };
    setOptions(updated);
  };

  const createRoom = async () => {
    if (!title.trim()) { setError('Please enter a game title'); return; }
    if (options.length < 2) { setError('Need at least 2 bet options'); return; }
    if (options.some(o => !o.label.trim())) { setError('All options need a label'); return; }

    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API}/api/rooms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, bet_options: options }),
      });
      const data = await res.json();
      // Store host_id in sessionStorage so the host page can use it
      sessionStorage.setItem(`host_${data.room_id}`, data.host_id);
      router.push(`/host/${data.room_id}`);
    } catch {
      setError('Failed to create room. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 mb-3 px-4 py-1.5 rounded-full"
          style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent)' }}>
          <span className="live-dot" />
          <span className="text-xs font-semibold tracking-widest uppercase" style={{ color: 'var(--accent-glow)' }}>
            BetLive
          </span>
        </div>
        <h1 className="text-5xl font-black tracking-tight mb-2" style={{ color: 'var(--text)' }}>
          Host a Game
        </h1>
        <p style={{ color: 'var(--text-muted)' }}>Set up bets, share your QR code, let up to 8 players join.</p>
      </div>

      {/* Form Card */}
      <div className="card p-8 w-full max-w-lg">
        <div className="space-y-5">
          {/* Title */}
          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>
              GAME TITLE
            </label>
            <input
              className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-all"
              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
              placeholder="e.g. World Cup Final — Who Scores First?"
              value={title}
              onChange={e => setTitle(e.target.value)}
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>
              DESCRIPTION <span className="font-normal">(optional)</span>
            </label>
            <textarea
              className="w-full px-4 py-3 rounded-lg text-sm outline-none resize-none"
              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
              placeholder="Extra context for players..."
              rows={2}
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </div>

          {/* Bet Options */}
          <div>
            <label className="block text-sm font-semibold mb-3" style={{ color: 'var(--text-muted)' }}>
              BET OPTIONS
            </label>
            <div className="space-y-2">
              {options.map((opt, i) => (
                <div key={opt.id} className="flex items-center gap-2">
                  <input
                    className="flex-1 px-3 py-2.5 rounded-lg text-sm outline-none"
                    style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}
                    placeholder={`Option ${i + 1} label`}
                    value={opt.label}
                    onChange={e => updateOption(i, 'label', e.target.value)}
                  />
                  <div className="flex items-center gap-1 px-3 py-2.5 rounded-lg text-sm"
                    style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>×</span>
                    <input
                      type="number"
                      step="0.1"
                      min="1.1"
                      className="w-14 bg-transparent outline-none text-center"
                      style={{ color: 'var(--accent-glow)' }}
                      value={opt.odds}
                      onChange={e => updateOption(i, 'odds', parseFloat(e.target.value))}
                    />
                  </div>
                  {options.length > 2 && (
                    <button
                      onClick={() => removeOption(i)}
                      className="w-9 h-9 flex items-center justify-center rounded-lg transition-colors"
                      style={{ background: 'var(--red-soft)', color: 'var(--red)' }}
                    >✕</button>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={addOption}
              className="mt-3 w-full py-2 rounded-lg text-sm font-medium transition-colors"
              style={{ border: '1px dashed var(--border)', color: 'var(--text-muted)' }}
            >
              + Add Option
            </button>
          </div>

          {error && (
            <div className="px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--red-soft)', color: 'var(--red)' }}>
              {error}
            </div>
          )}

          <button
            onClick={createRoom}
            disabled={loading}
            className="btn-primary w-full py-3.5 text-base glow-accent"
          >
            {loading ? 'Creating...' : '🎲 Create Game Room'}
          </button>
        </div>
      </div>

      <p className="mt-6 text-xs" style={{ color: 'var(--text-muted)' }}>
        Up to 8 players • Real-time WebSocket • Free to play
      </p>
    </main>
  );
}
