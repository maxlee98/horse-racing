'use client';

import { useEffect, useRef, useCallback } from 'react';
import { ROULETTE_WHEEL_ORDER, ROULETTE_COLORS } from '@/shared/types/game';

interface RouletteWheelProps {
  wheelRotation: number;
  ballPosition: number;
  ballRadius: number;
  phase: string | null;
  size?: number;
}

export default function RouletteWheel({
  wheelRotation,
  ballPosition,
  ballRadius,
  phase,
  size = 400
}: RouletteWheelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const centerX = size / 2;
  const centerY = size / 2;
  const outerRadius = size * 0.45;
  const innerRadius = size * 0.25;
  const pocketRadius = size * 0.35;

  const drawWheel = useCallback((ctx: CanvasRenderingContext2D) => {
    ctx.clearRect(0, 0, size, size);

    // Draw outer rim
    ctx.beginPath();
    ctx.arc(centerX, centerY, outerRadius, 0, Math.PI * 2);
    ctx.fillStyle = '#8B4513';
    ctx.fill();
    ctx.strokeStyle = '#5D3A1A';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw pockets
    const pocketAngle = (Math.PI * 2) / 38;
    
    ROULETTE_WHEEL_ORDER.forEach((num: number, index: number) => {
      const angle = (index * pocketAngle) - (Math.PI / 2) + (wheelRotation * Math.PI / 180);
      const color = ROULETTE_COLORS[num];
      
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, pocketRadius, angle, angle + pocketAngle);
      ctx.closePath();
      
      // Fill pocket color
      if (color === 'red') {
        ctx.fillStyle = '#DC2626';
      } else if (color === 'black') {
        ctx.fillStyle = '#1F2937';
      } else {
        ctx.fillStyle = '#059669';
      }
      ctx.fill();
      
      // Pocket border
      ctx.strokeStyle = '#D4AF37';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Draw number
      const textAngle = angle + pocketAngle / 2;
      const textRadius = pocketRadius * 0.75;
      const textX = centerX + Math.cos(textAngle) * textRadius;
      const textY = centerY + Math.sin(textAngle) * textRadius;
      
      ctx.save();
      ctx.translate(textX, textY);
      ctx.rotate(textAngle + Math.PI / 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.font = `bold ${size * 0.035}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const displayNum = num === 37 ? '00' : String(num);
      ctx.fillText(displayNum, 0, 0);
      ctx.restore();
    });

    // Draw inner circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
    ctx.fillStyle = '#8B4513';
    ctx.fill();
    ctx.strokeStyle = '#D4AF37';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw center spindle
    ctx.beginPath();
    ctx.arc(centerX, centerY, size * 0.05, 0, Math.PI * 2);
    ctx.fillStyle = '#D4AF37';
    ctx.fill();
    
    // Draw turret (center decoration)
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      const x = centerX + Math.cos(angle) * size * 0.08;
      const y = centerY + Math.sin(angle) * size * 0.08;
      ctx.beginPath();
      ctx.arc(x, y, size * 0.02, 0, Math.PI * 2);
      ctx.fillStyle = '#D4AF37';
      ctx.fill();
    }

    // Draw ball
    const ballAngle = (ballPosition * Math.PI / 180) - (Math.PI / 2);
    const normalizedRadius = Math.max(60, Math.min(100, ballRadius));
    const ballDistance = innerRadius + (pocketRadius - innerRadius) * (normalizedRadius / 100);
    const ballX = centerX + Math.cos(ballAngle) * ballDistance;
    const ballY = centerY + Math.sin(ballAngle) * ballDistance;
    
    // Ball shadow
    ctx.beginPath();
    ctx.arc(ballX + 2, ballY + 2, size * 0.025, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.fill();
    
    // Ball
    ctx.beginPath();
    ctx.arc(ballX, ballY, size * 0.025, 0, Math.PI * 2);
    const ballGradient = ctx.createRadialGradient(
      ballX - size * 0.008, ballY - size * 0.008, 0,
      ballX, ballY, size * 0.025
    );
    ballGradient.addColorStop(0, '#FFFFFF');
    ballGradient.addColorStop(0.3, '#E8E8E8');
    ballGradient.addColorStop(1, '#A0A0A0');
    ctx.fillStyle = ballGradient;
    ctx.fill();
    
    // Ball highlight
    ctx.beginPath();
    ctx.arc(ballX - size * 0.008, ballY - size * 0.008, size * 0.008, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.fill();

    // Draw decorative diamonds
    const diamondCount = 8;
    for (let i = 0; i < diamondCount; i++) {
      const angle = (i / diamondCount) * Math.PI * 2;
      const diamondRadius = outerRadius + size * 0.025;
      const dx = centerX + Math.cos(angle) * diamondRadius;
      const dy = centerY + Math.sin(angle) * diamondRadius;
      
      ctx.save();
      ctx.translate(dx, dy);
      ctx.rotate(angle);
      ctx.beginPath();
      ctx.moveTo(0, -size * 0.015);
      ctx.lineTo(size * 0.01, 0);
      ctx.lineTo(0, size * 0.015);
      ctx.lineTo(-size * 0.01, 0);
      ctx.closePath();
      ctx.fillStyle = '#D4AF37';
      ctx.fill();
      ctx.restore();
    }
  }, [centerX, centerY, outerRadius, innerRadius, pocketRadius, size, wheelRotation, ballPosition, ballRadius]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    drawWheel(ctx);
  }, [drawWheel]);

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      className="rounded-full shadow-2xl"
      style={{
        boxShadow: '0 0 50px rgba(212, 175, 55, 0.3), inset 0 0 30px rgba(0, 0, 0, 0.5)'
      }}
    />
  );
}
