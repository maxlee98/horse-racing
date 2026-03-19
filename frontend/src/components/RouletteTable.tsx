'use client';

import { ROULETTE_COLORS, ROULETTE_PAYOUTS, type RouletteBetType } from '@/types/game';

interface RouletteTableProps {
  selectedOption: string;
  onSelectOption: (optionId: string, betType: RouletteBetType, betNumber?: number) => void;
  disabled: boolean;
  betOptions: Array<{ id: string; label: string; odds: number }>;
}

export default function RouletteTable({
  selectedOption,
  onSelectOption,
  disabled,
  betOptions
}: RouletteTableProps) {
  const getNumberColor = (num: number): string => {
    return ROULETTE_COLORS[num] || 'green';
  };

  const handleNumberClick = (num: number) => {
    if (disabled) return;
    const option = betOptions.find(o => o.label === String(num) || o.id === String(num));
    if (option) {
      onSelectOption(option.id, 'single', num);
    }
  };

  const handleBetTypeClick = (betType: RouletteBetType) => {
    if (disabled) return;
    const option = betOptions.find(o => o.label.toLowerCase().replace(/\s+/g, '_') === betType);
    if (option) {
      onSelectOption(option.id, betType);
    }
  };

  const isSelected = (optionId: string) => selectedOption === optionId;

  // Column layout
  const column1 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34];
  const column2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35];
  const column3 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36];

  const NumberCell = ({ num }: { num: number }) => {
    const color = getNumberColor(num);
    const displayNum = num === 37 ? '00' : String(num);
    const option = betOptions.find(o => o.label === String(num) || o.id === String(num));
    const selected = option ? isSelected(option.id) : false;

    return (
      <button
        onClick={() => handleNumberClick(num)}
        disabled={disabled || !option}
        className={`
          relative w-full aspect-square flex items-center justify-center
          text-sm font-bold text-white border border-[#D4AF37]
          transition-all duration-150
          ${color === 'red' ? 'bg-red-600 hover:bg-red-500' : ''}
          ${color === 'black' ? 'bg-gray-900 hover:bg-gray-800' : ''}
          ${color === 'green' ? 'bg-green-600 hover:bg-green-500' : ''}
          ${selected ? 'ring-2 ring-yellow-400 ring-inset scale-95' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        {displayNum}
      </button>
    );
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      {/* Main table grid */}
      <div className="bg-green-800 rounded-lg p-4 shadow-2xl border-4 border-[#8B4513]">
        {/* Zero and Double Zero row */}
        <div className="flex gap-1 mb-1">
          <button
            onClick={() => handleNumberClick(0)}
            disabled={disabled}
            className={`
              w-12 h-24 flex items-center justify-center
              text-sm font-bold text-white border border-[#D4AF37]
              bg-green-600 hover:bg-green-500
              ${isSelected(betOptions.find(o => o.label === '0')?.id || '') ? 'ring-2 ring-yellow-400 ring-inset' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            0
          </button>
          <button
            onClick={() => handleNumberClick(37)}
            disabled={disabled}
            className={`
              w-12 h-24 flex items-center justify-center
              text-sm font-bold text-white border border-[#D4AF37]
              bg-green-600 hover:bg-green-500
              ${isSelected(betOptions.find(o => o.label === '00')?.id || '') ? 'ring-2 ring-yellow-400 ring-inset' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            00
          </button>
          
          {/* Number grid */}
          <div className="flex gap-1 flex-1">
            {/* Column 3 */}
            <div className="flex flex-col gap-1 flex-1">
              {column3.map(num => (
                <NumberCell key={num} num={num} />
              ))}
            </div>
            {/* Column 2 */}
            <div className="flex flex-col gap-1 flex-1">
              {column2.map(num => (
                <NumberCell key={num} num={num} />
              ))}
            </div>
            {/* Column 1 */}
            <div className="flex flex-col gap-1 flex-1">
              {column1.map(num => (
                <NumberCell key={num} num={num} />
              ))}
            </div>
          </div>
        </div>

        {/* Dozens */}
        <div className="flex gap-1 mt-1">
          <button
            onClick={() => handleBetTypeClick('first_dozen')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase().includes('1st') || o.label.toLowerCase().includes('first'))?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            1st 12
          </button>
          <button
            onClick={() => handleBetTypeClick('second_dozen')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase().includes('2nd') || o.label.toLowerCase().includes('second'))?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            2nd 12
          </button>
          <button
            onClick={() => handleBetTypeClick('third_dozen')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase().includes('3rd') || o.label.toLowerCase().includes('third'))?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            3rd 12
          </button>
        </div>

        {/* Even money bets */}
        <div className="flex gap-1 mt-1">
          <button
            onClick={() => handleBetTypeClick('low')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase().includes('1-18'))?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            1-18
          </button>
          <button
            onClick={() => handleBetTypeClick('even')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase() === 'even')?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            EVEN
          </button>
          <button
            onClick={() => handleBetTypeClick('red')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-red-600 hover:bg-red-500
              ${isSelected(betOptions.find(o => o.label.toLowerCase() === 'red')?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-red-500' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            RED
          </button>
          <button
            onClick={() => handleBetTypeClick('black')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-gray-900 hover:bg-gray-800
              ${isSelected(betOptions.find(o => o.label.toLowerCase() === 'black')?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-gray-800' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            BLACK
          </button>
          <button
            onClick={() => handleBetTypeClick('odd')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase() === 'odd')?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            ODD
          </button>
          <button
            onClick={() => handleBetTypeClick('high')}
            disabled={disabled}
            className={`
              flex-1 py-3 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase().includes('19-36'))?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            19-36
          </button>
        </div>

        {/* Column bets */}
        <div className="flex gap-1 mt-1 ml-14">
          <button
            onClick={() => handleBetTypeClick('first_column')}
            disabled={disabled}
            className={`
              flex-1 py-2 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase().includes('column 1') || o.label.toLowerCase().includes('1st column'))?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            2 to 1
          </button>
          <button
            onClick={() => handleBetTypeClick('second_column')}
            disabled={disabled}
            className={`
              flex-1 py-2 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase().includes('column 2') || o.label.toLowerCase().includes('2nd column'))?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            2 to 1
          </button>
          <button
            onClick={() => handleBetTypeClick('third_column')}
            disabled={disabled}
            className={`
              flex-1 py-2 text-sm font-bold text-white border border-[#D4AF37]
              bg-green-700 hover:bg-green-600
              ${isSelected(betOptions.find(o => o.label.toLowerCase().includes('column 3') || o.label.toLowerCase().includes('3rd column'))?.id || '') ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            2 to 1
          </button>
        </div>
      </div>

      {/* Payout info */}
      <div className="mt-4 text-center text-xs text-gray-400">
        <p>Straight: 35:1 | Split: 17:1 | Street: 11:1 | Corner: 8:1</p>
        <p>Line: 5:1 | Dozen/Column: 2:1 | Even Money: 1:1</p>
      </div>
    </div>
  );
}
