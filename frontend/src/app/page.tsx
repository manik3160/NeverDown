'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight, CheckCircle, ShieldAlert, Zap, Github, Cpu } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-black text-white selection:bg-cyan-500/30">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-cyan-900/30 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-900/30 rounded-full blur-[120px]" />
      </div>

      {/* Navbar */}
      <header className="relative z-10 container mx-auto px-6 py-6 flex justify-between items-center">
        <div className="flex items-center gap-2 font-bold text-xl tracking-tighter">
          <Zap className="w-6 h-6 text-cyan-400" />
          <span>NEVERDOWN</span>
        </div>
        <nav className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-white transition-colors">How it Works</a>
          <a href="https://github.com" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">GitHub</a>
        </nav>
        <Button asChild variant="outline" className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-950/30 hover:text-cyan-300">
          <Link href="/dashboard">Enter Console</Link>
        </Button>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 flex-1 flex flex-col justify-center items-center text-center px-6 pt-20 pb-32">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto space-y-8"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/20 text-cyan-400 text-xs font-medium mb-4">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
            Autonomous Infrastructure Healing v1.0
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-cyan-100 to-cyan-500/50">
            Downtime is <br className="hidden md:block" />
            <span className="text-cyan-400">Simply Optional.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            NeverDown automatically detects, analyzes, and patches infrastructure failures in real-time. 
            Stop waking up your on-call engineers at 3 AM.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-8">
            <Button asChild size="lg" className="h-12 px-8 text-base bg-cyan-600 hover:bg-cyan-500 text-white border-0 shadow-[0_0_20px_rgba(8,145,178,0.5)]">
               <Link href="/dashboard">
                 Start for Free <ArrowRight className="ml-2 w-4 h-4" />
               </Link>
            </Button>
            <Button asChild variant="ghost" size="lg" className="h-12 px-8 text-base text-gray-400 hover:text-white hover:bg-white/5">
               <a href="https://github.com" target="_blank" rel="noreferrer">
                 <Github className="mr-2 w-5 h-5" /> View on GitHub
               </a>
            </Button>
          </div>
        </motion.div>

        {/* Feature Grid */}
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-32 max-w-6xl mx-auto w-full"
          id="features"
        >
          {[
            {
              icon: ShieldAlert,
              title: "Instant Detection",
              desc: "Monitors logs and metrics to identify anomalies before they become outages."
            },
            {
              icon: Cpu,
              title: "AI Analysis",
              desc: "Deep traces execution paths to pinpoint the exact root cause in seconds."
            },
            {
              icon: CheckCircle,
              title: "Automated Fixes",
              desc: "Generates, verifies, and deploys patches autonomously with safety checks."
            }
          ].map((feature, i) => (
            <div key={i} className="p-6 rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 transition-colors text-left">
              <feature.icon className="w-10 h-10 text-cyan-400 mb-4" />
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-gray-400 leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 py-8 text-center text-sm text-gray-500">
        <div className="container mx-auto">
          &copy; {new Date().getFullYear()} NeverDown. Built for the Thapar Hackathon.
        </div>
      </footer>
    </div>
  );
}
