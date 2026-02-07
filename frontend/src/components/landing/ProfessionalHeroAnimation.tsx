'use client';

import { motion } from 'framer-motion';
import { Zap, Shield, Search, Brain, CheckCircle2 } from 'lucide-react';

export function ProfessionalHeroAnimation() {
  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none">
      {/* Background Dots - More Elegant than Grid */}
      <div 
        className="absolute inset-0 opacity-[0.15]"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, white 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }}
      />
      
      {/* Ethereal Orbs */}
      <motion.div 
        animate={{ 
          scale: [1, 1.2, 1],
          x: [0, 50, 0],
          y: [0, -30, 0]
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        className="absolute -top-[10%] -right-[5%] w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[120px]"
      />

      {/* Central High-Fidelity Hub */}
      <div className="absolute right-[5%] lg:right-[15%] top-1/2 -translate-y-1/2 w-[450px] h-[450px] hidden lg:block">
        {/* Soft Glowing Atmosphere */}
        <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/5 to-purple-500/5 rounded-full blur-3xl animate-pulse" />
        
        {/* Ultra-Thin Orbital Rings */}
        {[100, 75, 50].map((radius, i) => (
          <div 
            key={i}
            className="absolute inset-0 border border-white/[0.03] rounded-full"
            style={{ margin: `${(100 - radius) / 2}%` }}
          />
        ))}

        {/* The Core Hub */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative">
             {/* Center Icon with Pulse */}
             <div className="w-20 h-20 bg-black border border-white/10 rounded-full flex items-center justify-center relative z-20 overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-t from-cyan-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <Zap className="w-8 h-8 text-white relative z-10" />
             </div>
             
             {/* Rotating Satellites - Very Subtle */}
             {[
               { icon: Shield, label: "01", delay: 0 },
               { icon: Search, label: "02", delay: 10 },
               { icon: Brain, label: "03", delay: 20 },
               { icon: CheckCircle2, label: "04", delay: 30 }
             ].map((agent, i) => (
               <motion.div
                 key={agent.label}
                 animate={{ rotate: 360 }}
                 transition={{ duration: 40, repeat: Infinity, ease: "linear", delay: -agent.delay }}
                 className="absolute inset-[-140px]"
               >
                 <div className="absolute top-0 left-1/2 -translate-x-1/2 flex flex-col items-center">
                    <div className="w-10 h-10 bg-black/60 backdrop-blur-md border border-white/5 rounded-full flex items-center justify-center rotate-[-360deg] shadow-[0_0_20px_rgba(255,255,255,0.02)]">
                       <agent.icon className="w-4 h-4 text-white/40" />
                    </div>
                 </div>
               </motion.div>
             ))}
          </div>
        </div>

        {/* Ethereal Particles */}
        {Array.from({ length: 15 }).map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: 0, y: 0 }}
            animate={{ 
              opacity: [0, 0.4, 0],
              x: (Math.random() - 0.5) * 300,
              y: (Math.random() - 0.5) * 300
            }}
            transition={{
              duration: 5 + Math.random() * 5,
              repeat: Infinity,
              delay: Math.random() * 5,
            }}
            className="absolute left-1/2 top-1/2 w-0.5 h-0.5 bg-white rounded-full"
          />
        ))}
      </div>

      {/* Global Masks */}
      <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-transparent z-0 hidden lg:block" />
      <div className="absolute inset-0 bg-gradient-to-b from-black via-transparent to-black" />
    </div>
  );
}
