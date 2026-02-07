'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState, memo } from 'react';

const GRID_SIZE_X = 25; // More density
const GRID_SIZE_Y = 15;

interface Block {
  id: string;
  x: number;
  y: number;
  color: string;
}

const COLORS = [
  'bg-cyan-500/40',
  'bg-blue-500/40',
  'bg-purple-500/40',
  'bg-emerald-500/40',
];

export const InteractiveGrid = memo(function InteractiveGrid() {
  const [activeBlocks, setActiveBlocks] = useState<Block[]>([]);

  useEffect(() => {
    // Initial noise
    const initial: Block[] = [];
    for(let i = 0; i < 12; i++) {
      initial.push({
        id: Math.random().toString(),
        x: Math.floor(Math.random() * GRID_SIZE_X),
        y: Math.floor(Math.random() * GRID_SIZE_Y),
        color: COLORS[Math.floor(Math.random() * COLORS.length)]
      });
    }
    setActiveBlocks(initial);

    const interval = setInterval(() => {
      setActiveBlocks(prev => {
        const next = [...prev];
        if (next.length > 15) next.shift(); // Cycle out
        
        if (Math.random() < 0.6) {
          next.push({
            id: Math.random().toString(),
            x: Math.floor(Math.random() * GRID_SIZE_X),
            y: Math.floor(Math.random() * GRID_SIZE_Y),
            color: COLORS[Math.floor(Math.random() * COLORS.length)]
          });
        }
        return next;
      });
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="absolute inset-0 z-0 pointer-events-none opacity-40">
      <div 
        className="grid gap-[1px] w-full h-full border-white/5" 
        style={{ 
          gridTemplateColumns: `repeat(${GRID_SIZE_X}, 1fr)`,
          gridTemplateRows: `repeat(${GRID_SIZE_Y}, 1fr)`,
        }}
      >
        {Array.from({ length: GRID_SIZE_X * GRID_SIZE_Y }).map((_, i) => {
          const x = i % GRID_SIZE_X;
          const y = Math.floor(i / GRID_SIZE_X);
          const activeBlock = activeBlocks.find(b => b.x === x && b.y === y);

          return (
            <div 
              key={i} 
              className="relative aspect-square border-[0.5px] border-white/5 bg-transparent"
            >
              <AnimatePresence>
                {activeBlock && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1 }}
                    className={`absolute inset-0 ${activeBlock.color} backdrop-blur-[2px]`}
                  >
                    {/* Data line animation inside the block */}
                    <motion.div 
                        animate={{ x: ['-100%', '100%'] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="absolute h-full w-[20%] bg-white/20 blur-sm"
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
      
      {/* Vented mask to make it look "techy" */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-transparent to-black" />
      <div className="absolute inset-0 bg-gradient-to-r from-black via-transparent to-black" />
    </div>
  );
});
