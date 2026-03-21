'use client';

import { ROULETTE_WHEEL_ORDER, ROULETTE_COLORS } from '@/shared/types/game';

interface RouletteWheelProps {
  wheelRotation: number;
  ballPosition: number;
  ballRadius: number;
  phase?: string | null;
  size?: number;
}

/**
 * Animated Roulette Wheel Component
 * Displays the American roulette wheel with spinning animation
 */
export default function RouletteWheel({
  wheelRotation,
  ballPosition,
  ballRadius,
  phase,
  size = 300,
}: RouletteWheelProps) {
  const center = size / 2;
  const pocketAngle = 360 / 38;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <defs>
        {/* Ball gradient for 3D effect */}
        <radialGradient id="ballGradient" cx="30%" cy="30%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="50%" stopColor="#e5e5e5" />
          <stop offset="100%" stopColor="#a3a3a3" />
        </radialGradient>
        
        {/* Shadow for depth */}
        <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="2" dy="2" stdDeviation="3" floodOpacity="0.3"/>
        </filter>
      </defs>

      {/* Outer rim */}
      <circle
        cx={center}
        cy={center}
        r={center - 5}
        fill="none"
        stroke="#8B4513"
        strokeWidth="8"
      />

      {/* Rotating wheel group */}
      <g transform={`rotate(${wheelRotation}, ${center}, ${center})`}>
        {/* Wheel background */}
        <circle
          cx={center}
          cy={center}
          r={center - 15}
          fill="#1a1a1a"
        />

        {/* Number pockets */}
        {ROULETTE_WHEEL_ORDER.map((num, i) => {
          const angle = i * pocketAngle;
          const color = ROULETTE_COLORS[num];
          const label = num === 37 ? '00' : String(num);
          
          return (
            <g key={num} transform={`rotate(${angle}, ${center}, ${center})`}>
              {/* Pocket */}
              <path
                d={`M ${center} ${15} L ${center - 12} ${center - 25} A ${center - 25} ${center - 25} 0 0 1 ${center + 12} ${center - 25} Z`}
                fill={color === 'red' ? '#DC2626' : color === 'black' ? '#1F2937' : '#059669'}
                stroke="#B45309"
                strokeWidth="1"
              />
              {/* Number label */}
              <text
                x={center}
                y={45}
                textAnchor="middle"
                fill="white"
                fontSize="10"
                fontWeight="bold"
                transform={`rotate(90, ${center}, 45)`}
              >
                {label}
              </text>
            </g>
          );
        })}

        {/* Center hub */}
        <circle
          cx={center}
          cy={center}
          r={25}
          fill="#8B4513"
          stroke="#5D2F0D"
          strokeWidth="2"
        />
        <circle
          cx={center}
          cy={center}
          r={15}
          fill="#D2691E"
        />
      </g>

      {/* Ball - rotates opposite to wheel */}
      <g transform={`rotate(${-wheelRotation + ballPosition}, ${center}, ${center})`}>
        <circle
          cx={center}
          cy={center - ballRadius}
          r={6}
          fill="url(#ballGradient)"
          filter="url(#shadow)"
        />
      </g>
    </svg>
  );
}
