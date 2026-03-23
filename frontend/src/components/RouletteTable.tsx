'use client';

import { ROULETTE_COLORS, ROULETTE_PAYOUTS, ROULETTE_BET_ODDS, type RouletteBetType } from '@/types/game';

interface RouletteTableProps {
  selectedOption: string;
  onSelectOption: (optionId: string, betType: RouletteBetType, betNumber?: number) => void;
  disabled: boolean;
  betOptions: Array<{ id: string; label: string; odds: number }>;
  rouletteHistory?: string[];
}

export default function RouletteTable({
  selectedOption,
  onSelectOption,
  disabled,
  betOptions,
  rouletteHistory = []
}: RouletteTableProps) {
  const getNumberColor = (num: number): string => {
    return ROULETTE_COLORS[num] || 'green';
  };

  const getHistoryColor = (num: string): string => {
    // Handle '00' as 37
    const numVal = num === '00' ? 37 : parseInt(num);
    if (isNaN(numVal)) return 'bg-green-600';
    return ROULETTE_COLORS[numVal] === 'red' ? 'bg-red-600' : 
           ROULETTE_COLORS[numVal] === 'black' ? 'bg-gray-900' : 'bg-green-600';
  };

  const handleNumberClick = (num: number) => {
    if (disabled) return;
    // For 00, we use 37 internally but display as '00'
    const displayNum = num === 37 ? '00' : String(num);
    const option = betOptions.find(o => o.label === displayNum || o.id === displayNum || o.id === String(num));
    if (option) {
      onSelectOption(option.id, 'single', num);
    }
  };

  const handleBetTypeClick = (betType: RouletteBetType) => {
    if (disabled) return;
    
    // Map bet types to option labels
    const betTypeToLabel: Record<string, string[]> = {
      'red': ['red'],
      'black': ['black'],
      'even': ['even'],
      'odd': ['odd'],
      'low': ['1-18', 'low'],
      'high': ['19-36', 'high'],
      'first_dozen': ['1st 12', 'first 12'],
      'second_dozen': ['2nd 12', 'second 12'],
      'third_dozen': ['3rd 12', 'third 12'],
      'first_column': ['column 1', 'col1'],
      'second_column': ['column 2', 'col2'],
      'third_column': ['column 3', 'col3'],
    };
    
    const searchLabels = betTypeToLabel[betType] || [betType];
    const option = betOptions.find(o => {
      const optLabel = o.label.toLowerCase();
      return searchLabels.some(label => optLabel.includes(label.toLowerCase()));
    });
    
    if (option) {
      onSelectOption(option.id, betType);
    }
  };

  const isSelected = (optionId: string) => selectedOption === optionId;

  // Column layout - numbers that go in each column (bottom to top in display)
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
          w-full h-8 flex items-center justify-center
          text-xs font-bold text-white border border-[#D4AF37]
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

  const ZeroCell = ({ num }: { num: number }) => {
    const displayNum = num === 37 ? '00' : String(num);
    const selected = isSelected(betOptions.find(o => o.label === displayNum)?.id || '');
    
    return (
      <button
        onClick={() => handleNumberClick(num)}
        disabled={disabled}
        className={`
          w-full h-8 flex items-center justify-center
          text-xs font-bold text-white border border-[#D4AF37]
          bg-green-600 hover:bg-green-500
          ${selected ? 'ring-2 ring-yellow-400 ring-inset' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        {displayNum}
      </button>
    );
  };

  const DozenButton = ({ type, label }: { type: RouletteBetType; label: string }) => {
    const selected = isSelected(
      betOptions.find(o => {
        const lower = o.label.toLowerCase();
        if (type === 'first_dozen') return lower.includes('1st') || lower.includes('first');
        if (type === 'second_dozen') return lower.includes('2nd') || lower.includes('second');
        if (type === 'third_dozen') return lower.includes('3rd') || lower.includes('third');
        return false;
      })?.id || ''
    );
    
    return (
      <button
        onClick={() => handleBetTypeClick(type)}
        disabled={disabled}
        className={`
          py-2 px-1 text-xs font-bold text-white border border-[#D4AF37]
          bg-green-700 hover:bg-green-600
          ${selected ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        {label}
      </button>
    );
  };

  const EvenMoneyButton = ({ type, label, bgClass }: { type: RouletteBetType; label: string; bgClass: string }) => {
    const selected = isSelected(
      betOptions.find(o => {
        const lower = o.label.toLowerCase();
        if (type === 'low') return lower.includes('1-18');
        if (type === 'even') return lower === 'even';
        if (type === 'red') return lower === 'red';
        if (type === 'black') return lower === 'black';
        if (type === 'odd') return lower === 'odd';
        if (type === 'high') return lower.includes('19-36');
        return false;
      })?.id || ''
    );
    
    return (
      <button
        onClick={() => handleBetTypeClick(type)}
        disabled={disabled}
        className={`
          py-2 px-1 text-xs font-bold text-white border border-[#D4AF37]
          ${bgClass}
          ${selected ? 'ring-2 ring-yellow-400 ring-inset' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        {label}
      </button>
    );
  };

  const ColumnButton = ({ type }: { type: RouletteBetType }) => {
    const selected = isSelected(
      betOptions.find(o => {
        const lower = o.label.toLowerCase();
        if (type === 'first_column') return lower.includes('column 1') || lower.includes('1st column');
        if (type === 'second_column') return lower.includes('column 2') || lower.includes('2nd column');
        if (type === 'third_column') return lower.includes('column 3') || lower.includes('3rd column');
        return false;
      })?.id || ''
    );
    
    return (
      <button
        onClick={() => handleBetTypeClick(type)}
        disabled={disabled}
        className={`
          py-2 px-1 text-xs font-bold text-white border border-[#D4AF37]
          bg-green-700 hover:bg-green-600
          ${selected ? 'ring-2 ring-yellow-400 ring-inset bg-green-600' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        2 to 1
      </button>
    );
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      {/* Main table grid using CSS Grid */}
      <div className="bg-green-800 rounded-lg p-3 shadow-2xl border-4 border-[#8B4513]">
        {/* Grid: [zeros | col3 | col2 | col1] */}
        <div className="grid grid-cols-[1fr_1fr_1fr_1fr] gap-0.5">
          
          {/* Row 1: 0 and 00 combined, and column headers (2 to 1) */}
          <div className="flex gap-0.5">
            <ZeroCell num={0} />
            <ZeroCell num={37} />
          </div>
          <ColumnButton type="third_column" />
          <ColumnButton type="second_column" />
          <ColumnButton type="first_column" />
          
          {/* Number rows */}
          {[...Array(12)].map((_, rowIndex) => (
            <>
              {/* Empty space in zero column */}
              <div key={`zero-${rowIndex}`} className="h-10" />
              
              {/* Column 3 numbers (displayed top to bottom) */}
              <NumberCell key={`c3-${rowIndex}`} num={column3[11 - rowIndex]} />
              
              {/* Column 2 numbers */}
              <NumberCell key={`c2-${rowIndex}`} num={column2[11 - rowIndex]} />
              
              {/* Column 1 numbers */}
              <NumberCell key={`c1-${rowIndex}`} num={column1[11 - rowIndex]} />
            </>
          ))}
          
          {/* Dozens row */}
          <div className="col-span-4 grid grid-cols-3 gap-0.5 mt-1">
            <DozenButton type="first_dozen" label="1st 12" />
            <DozenButton type="second_dozen" label="2nd 12" />
            <DozenButton type="third_dozen" label="3rd 12" />
          </div>
          
          {/* Even money bets row */}
          <div className="col-span-4 grid grid-cols-6 gap-0.5 mt-1">
            <EvenMoneyButton type="low" label="1-18" bgClass="bg-green-700 hover:bg-green-600" />
            <EvenMoneyButton type="even" label="EVEN" bgClass="bg-green-700 hover:bg-green-600" />
            <EvenMoneyButton type="red" label="RED" bgClass="bg-red-600 hover:bg-red-500" />
            <EvenMoneyButton type="black" label="BLACK" bgClass="bg-gray-900 hover:bg-gray-800" />
            <EvenMoneyButton type="odd" label="ODD" bgClass="bg-green-700 hover:bg-green-600" />
            <EvenMoneyButton type="high" label="19-36" bgClass="bg-green-700 hover:bg-green-600" />
          </div>
        </div>
      </div>

      {/* Roulette History */}
      {rouletteHistory.length > 0 && (
        <div className="mt-4 p-3 bg-[#1a1a2e] rounded-lg border border-[#D4AF37]">
          <p className="text-xs font-semibold text-gray-400 mb-2 text-center">Recent Results</p>
          <div className="flex flex-wrap justify-center gap-1">
            {[...rouletteHistory].reverse().map((num, idx) => (
              <div
                key={`${num}-${idx}`}
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center
                  text-xs font-bold text-white border border-[#D4AF37]
                  ${getHistoryColor(num)}
                  ${idx === 0 ? 'ring-2 ring-yellow-400 ring-offset-1 ring-offset-[#1a1a2e]' : ''}
                `}
              >
                {num}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Payout info */}
      <div className="mt-4 text-center text-xs text-gray-400">
        <p>Straight: 35:1 | Split: 17:1 | Street: 11:1 | Corner: 8:1</p>
        <p>Line: 5:1 | Dozen/Column: 2:1 | Even Money: 1:1</p>
      </div>
    </div>
  );
}
