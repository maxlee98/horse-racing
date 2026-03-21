/**
 * API client for backend communication
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  baseUrl: API_BASE,

  async createRoom(data: {
    title: string;
    description: string;
    bet_options: Array<{ id: string; label: string; odds: number }>;
    game_mode: string;
    use_randomized_probabilities: boolean;
  }) {
    const res = await fetch(`${API_BASE}/api/rooms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create room');
    return res.json();
  },

  async getRoom(roomId: string) {
    const res = await fetch(`${API_BASE}/api/rooms/${roomId}`);
    if (!res.ok) throw new Error('Room not found');
    return res.json();
  },

  async getQRCode(roomId: string, baseUrl: string) {
    const res = await fetch(`${API_BASE}/api/rooms/${roomId}/qr?base_url=${encodeURIComponent(baseUrl)}`);
    if (!res.ok) throw new Error('Failed to generate QR');
    return res.json() as Promise<{ qr_base64: string; join_url: string }>;
  },

  async updateProbabilities(
    roomId: string,
    probabilities: Record<string, number>,
    hostId: string
  ) {
    const res = await fetch(`${API_BASE}/api/rooms/${roomId}/probabilities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ probabilities, host_id: hostId }),
    });
    if (!res.ok) throw new Error('Failed to update probabilities');
    return res.json();
  },

  async getConstants() {
    const res = await fetch(`${API_BASE}/api/constants`);
    if (!res.ok) throw new Error('Failed to fetch constants');
    return res.json();
  },
};
