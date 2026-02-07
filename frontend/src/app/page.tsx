'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { 
  ArrowRight, 
  CheckCircle, 
  ShieldAlert, 
  Zap, 
  Github, 
  Cpu, 
  Terminal, 
  History,
  Activity,
  ChevronRight
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';

export default function LandingPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  const opacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.2], [1, 0.9]);

  return (
    <div ref={containerRef} className="flex flex-col min-h-screen bg-[#050510] text-white selection:bg-cyan-500/30 overflow-x-hidden">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute top-[10%] left-[-10%] w-[60%] h-[60%] bg-cyan-600/10 rounded-full blur-[140px] animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-blue-600/10 rounded-full blur-[140px] animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full opacity-[0.03] pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')] bg-repeat" />
      </div>

      {/* Navbar */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[#050510]/60 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2 font-bold text-xl tracking-tighter">
            <div className="bg-cyan-500 p-1.5 rounded-lg">
              <Zap className="w-5 h-5 text-[#050510] fill-[#050510]" />
            </div>
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">NEVERDOWN</span>
          </div>
          <nav className="hidden md:flex gap-10 text-sm font-medium text-gray-400">
            <a href="#features" className="hover:text-cyan-400 transition-colors">Technology</a>
            <a href="#workflow" className="hover:text-cyan-400 transition-colors">Workflow</a>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="hover:text-cyan-400 transition-colors">Open Source</a>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Sign In</Link>
            <Button asChild size="sm" className="bg-white text-black hover:bg-gray-200 border-0 rounded-full px-5">
              <Link href="/dashboard">Launch Console</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 pt-32">
        <section className="container mx-auto px-6 pt-20 pb-40 flex flex-col items-center text-center">
          <motion.div 
            style={{ opacity, scale }}
            className="max-w-4xl mx-auto space-y-10"
          >
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-cyan-500/20 bg-cyan-500/5 text-cyan-400 text-[10px] uppercase tracking-[0.2em] font-bold"
            >
              <Activity className="w-3 h-3" />
              Next-Gen Observability & Patching
            </motion.div>
            
            <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight leading-[1.1] mb-8">
              Reliability <br />
              <span className="italic text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-400 bg-[length:200%_auto] animate-gradient">
                On Autopilot.
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto leading-relaxed font-light">
              NeverDown is the first autonomous agent system that detects, explains, and 
              repairs infrastructure failures before they affect your users.
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center pt-8">
              <Button asChild size="lg" className="h-14 px-10 text-lg bg-cyan-500 hover:bg-cyan-400 text-[#050510] border-0 rounded-full transition-all hover:scale-105 hover:shadow-[0_0_40px_rgba(6,182,212,0.4)]">
                 <Link href="/dashboard">
                   Start Integration <ArrowRight className="ml-2 w-5 h-5" />
                 </Link>
              </Button>
              <Button asChild variant="ghost" size="lg" className="h-14 px-10 text-lg text-gray-400 hover:text-white hover:bg-white/5 border border-white/10 rounded-full">
                 <a href="https://github.com" target="_blank" rel="noreferrer">
                   <Github className="mr-2 w-6 h-6" /> Star on GitHub
                 </a>
              </Button>
            </div>
            
            {/* Stats/Proof */}
            <div className="pt-20 grid grid-cols-2 md:grid-cols-4 gap-8 opacity-60">
               <div className="flex flex-col items-center">
                  <span className="text-3xl font-bold">99.99%</span>
                  <span className="text-xs text-gray-500 uppercase tracking-widest mt-1">Target Uptime</span>
               </div>
               <div className="flex flex-col items-center">
                  <span className="text-3xl font-bold">&lt; 30s</span>
                  <span className="text-xs text-gray-500 uppercase tracking-widest mt-1">Mean Time to Fix</span>
               </div>
               <div className="flex flex-col items-center">
                  <span className="text-3xl font-bold">Zero</span>
                  <span className="text-xs text-gray-500 uppercase tracking-widest mt-1">Manual Intervention</span>
               </div>
               <div className="flex flex-col items-center">
                  <span className="text-3xl font-bold">100%</span>
                  <span className="text-xs text-gray-500 uppercase tracking-widest mt-1">Verified Patches</span>
               </div>
            </div>
          </motion.div>
        </section>

        {/* Feature Bento Grid */}
        <section id="features" className="container mx-auto px-6 py-40">
           <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Feature 1: Large */}
              <motion.div 
                whileInView={{ opacity: 1, y: 0 }}
                initial={{ opacity: 0, y: 20 }}
                viewport={{ once: true }}
                className="md:col-span-2 p-10 rounded-[2rem] border border-white/5 bg-gradient-to-br from-white/10 to-transparent backdrop-blur-sm group"
              >
                 <div className="flex justify-between items-start mb-20">
                    <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20">
                       <Cpu className="w-10 h-10 text-cyan-400" />
                    </div>
                    <Badge className="bg-cyan-500/20 text-cyan-400 border-cyan-500/30">AI Orchestrator</Badge>
                 </div>
                 <h3 className="text-4xl font-bold mb-6">Multi-Agent Intelligence</h3>
                 <p className="text-gray-400 text-lg leading-relaxed max-w-xl">
                    Our system uses a specialized swarm of agents—Detective, Reasoner, Surgeon, and Verifier—to handle the entire incident lifecycle without context loss.
                 </p>
              </motion.div>

              {/* Feature 2: Small */}
              <motion.div 
                whileInView={{ opacity: 1, y: 0 }}
                initial={{ opacity: 0, y: 20 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                className="p-10 rounded-[2rem] border border-white/5 bg-gradient-to-br from-white/5 to-transparent backdrop-blur-sm"
              >
                 <ShieldAlert className="w-12 h-12 text-blue-400 mb-20" />
                 <h3 className="text-2xl font-bold mb-4">Secret Sanitization</h3>
                 <p className="text-gray-400 leading-relaxed">
                    Automatic PII and secret removal from logs before analysis to ensure your data stays secure.
                 </p>
              </motion.div>

              {/* Feature 3: Small */}
              <motion.div 
                whileInView={{ opacity: 1, y: 0 }}
                initial={{ opacity: 0, y: 20 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="p-10 rounded-[2rem] border border-white/5 bg-gradient-to-br from-white/5 to-transparent backdrop-blur-sm"
              >
                 <Terminal className="w-12 h-12 text-purple-400 mb-20" />
                 <h3 className="text-2xl font-bold mb-4">Shadow Sandbox</h3>
                 <p className="text-gray-400 leading-relaxed">
                    Isolated environments created on-demand to verify patches before they touch production.
                 </p>
              </motion.div>

              {/* Feature 4: Large */}
              <motion.div 
                whileInView={{ opacity: 1, y: 0 }}
                initial={{ opacity: 0, y: 20 }}
                viewport={{ once: true }}
                transition={{ delay: 0.3 }}
                className="md:col-span-2 p-10 rounded-[2rem] border border-white/5 bg-gradient-to-br from-white/10 to-transparent backdrop-blur-sm"
              >
                 <div className="flex justify-between items-start mb-20">
                    <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20">
                       <History className="w-10 h-10 text-blue-400" />
                    </div>
                    <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">Continuous Learning</Badge>
                 </div>
                 <h3 className="text-4xl font-bold mb-6">Autonomous Feedback Loop</h3>
                 <p className="text-gray-400 text-lg leading-relaxed max-w-xl">
                    Every resolution is audit-trailed and used to improve the system's reasoning capabilities, making your infrastructure resilient over time.
                 </p>
              </motion.div>
           </div>
        </section>

        {/* Call to Action */}
        <section className="container mx-auto px-6 py-40 text-center">
            <div className="p-20 rounded-[3rem] border border-white/10 bg-gradient-to-t from-cyan-500/10 to-transparent relative overflow-hidden">
                <div className="relative z-10 space-y-8">
                    <h2 className="text-4xl md:text-6xl font-extrabold tracking-tight">Ready to kill the outage?</h2>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Connect your GitHub repository and infrastructure monitoring in minutes. 
                        Let NeverDown handle the 3 AM alerts.
                    </p>
                    <Button asChild size="lg" className="h-16 px-12 text-xl bg-white text-black hover:bg-gray-100 border-0 rounded-full">
                       <Link href="/dashboard">Get Access Now</Link>
                    </Button>
                </div>
                {/* Decorative Elements */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-600/10 blur-[100px] rounded-full" />
            </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-12">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8 text-sm text-gray-500">
           <div className="flex items-center gap-2 font-bold text-white text-lg tracking-tighter">
             <div className="bg-white p-1 rounded">
               <Zap className="w-4 h-4 text-black fill-black" />
             </div>
             NEVERDOWN
           </div>
           <div className="flex gap-10">
              <a href="#" className="hover:text-white transition-colors">Documentation</a>
              <a href="#" className="hover:text-white transition-colors">API Reference</a>
              <a href="#" className="hover:text-white transition-colors">Changelog</a>
           </div>
           <div>
             &copy; {new Date().getFullYear()} Autonomous Infrastructure Systems.
           </div>
        </div>
      </footer>
    </div>
  );
}
