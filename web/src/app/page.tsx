"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function LandingPage() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 50) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="bg-white text-black min-h-screen font-sans selection:bg-[#ff6b00] selection:text-white">
      {/* Navigation */}
      <header className="flex items-center justify-between px-6 md:px-12 py-6 border-b border-gray-100 bg-white sticky top-0 z-50">
        <div className="flex items-center gap-12">
          <Link href="/" className="font-bold text-xl md:text-2xl tracking-tight font-serif text-black">NeverDown</Link>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-500">
            <Link href="#product" className="hover:text-black transition-colors">Product</Link>
            <Link href="#pipeline" className="hover:text-black transition-colors">Pipeline</Link>
            <Link href="#" className="hover:text-black transition-colors">Pricing</Link>
            <Link href="#" className="hover:text-black transition-colors">Resources</Link>
          </nav>
        </div>
        <div className="flex items-center gap-6 text-sm font-medium">
          <Link href="/dashboard" className="text-gray-600 hover:text-black transition-colors font-bold">Login</Link>
          <Link href="/dashboard" className="bg-[#111] text-white px-5 py-2.5 rounded-md hover:bg-black transition-colors flex items-center gap-2">
            Get early access <span className="text-[#ff6b00]">→</span>
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 pt-20 pb-24">
        {/* Hero Section */}
        <section className="text-center max-w-4xl mx-auto flex flex-col items-center">
          <h1 className="text-5xl md:text-7xl font-serif tracking-tight leading-[1.1] mb-6">
            <span className="text-black font-bold block">Autonomous Incident</span>
            <span className="text-black font-bold block mb-2">Remediation.</span>
            <span className={`font-bold transition-colors duration-500 ${isScrolled ? 'text-[#ff6b00]' : 'text-gray-400'}`}>Fixed before you wake up.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-500 max-w-2xl mx-auto mb-10 leading-relaxed font-medium">
            A modern SRE platform that replaces manual on-call shifts, noisy 
            alerts, and lost sleep with one clean, autonomous engine your team 
            can rely on every single night.
          </p>
          
          <Link href="/dashboard" className="bg-[#111] text-white px-8 py-4 rounded-lg text-lg font-medium hover:bg-black transition-colors flex items-center gap-3 shadow-xl shadow-black/5">
            Try it Now <span className="bg-[#ff6b00] text-white w-6 h-6 flex items-center justify-center rounded text-sm">→</span>
          </Link>
        </section>

        {/* Integration Logos */}
        <section className="mt-28 border-t border-gray-100 pt-12 overflow-hidden">
          <div className="relative w-full flex items-center h-16
                          before:absolute before:left-0 before:top-0 before:z-10 before:h-full before:w-16 before:md:w-32 before:bg-gradient-to-r before:from-white before:to-transparent
                          after:absolute after:right-0 after:top-0 after:z-10 after:h-full after:w-16 after:md:w-32 after:bg-gradient-to-l after:from-white after:to-transparent">
            <motion.div 
              className="flex w-fit"
              animate={{ x: ["0%", "-50%"] }}
              transition={{ ease: "linear", duration: 25, repeat: Infinity }}
            >
              {[0, 1].map((setIndex) => (
                <div key={setIndex} className="flex gap-16 md:gap-32 pr-16 md:pr-32 shrink-0 items-center opacity-30 grayscale hover:grayscale-0 transition-all duration-300">
                  <span className="text-2xl font-semibold font-sans tracking-tight cursor-default">Datadog</span>
                  <span className="text-2xl font-semibold font-sans tracking-tight cursor-default">PagerDuty</span>
                  <span className="text-2xl font-bold font-sans tracking-tight cursor-default">splunk</span>
                  <span className="text-2xl font-bold font-sans tracking-wider cursor-default">AWS</span>
                  <span className="text-2xl font-bold font-sans tracking-tight text-[#ff6b00] cursor-default">Cloudflare</span>
                  <span className="text-2xl font-semibold font-sans tracking-tight cursor-default">kubernetes</span>
                </div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Features Section */}
        <section id="product" className="mt-36 pt-16 border-t border-gray-100">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <div className="text-[#ff6b00] text-xs font-bold tracking-[0.15em] uppercase mb-6">Built for Clarity</div>
            <h2 className="text-4xl md:text-[3.5rem] leading-[1.1] font-serif font-bold text-black mb-8">
              The way incident response should&apos;ve worked from the start
            </h2>
            <p className="text-gray-500 text-lg md:text-xl font-medium">
              A streamlined workflow where engineers always know what&apos;s next, what&apos;s fixed, and what matters.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-[#fafafa] rounded-3xl p-8 border border-gray-100 shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)] flex flex-col items-center text-center">
              <div className="w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-10 space-y-3">
                <div className="flex justify-between items-center bg-gray-50 rounded-xl p-3.5 border border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="w-4 h-4 rounded-[4px] bg-[#ff6b00]/10 flex items-center justify-center"><div className="w-2 h-2 rounded-full bg-[#ff6b00]"></div></div>
                    <span className="text-sm font-semibold text-gray-800">Auto-remediation logs (12)</span>
                  </div>
                  <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center">
                    <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  </div>
                </div>
                <div className="flex justify-between items-center bg-gray-50 rounded-xl p-3.5 border border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="w-4 h-4 rounded-[4px] bg-blue-100 flex items-center justify-center"><div className="w-2 h-2 rounded-full bg-blue-500"></div></div>
                    <span className="text-sm font-semibold text-gray-800">Recent health-checks (4)</span>
                  </div>
                  <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center">
                    <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  </div>
                </div>
              </div>
              <h3 className="text-2xl font-bold font-serif mb-4 text-black">Centralize your infrastructure</h3>
              <p className="text-gray-500 text-base leading-relaxed">
                Connect your entire stack in minutes. From cloud providers to monitoring tools, everything lives in one organized space.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-[#fafafa] rounded-3xl p-8 border border-gray-100 shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)] flex flex-col items-center text-center">
              <div className="w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-10">
                <div className="flex items-center gap-2 mb-6">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                    <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  </div>
                  <span className="text-[11px] font-bold text-gray-400 tracking-wider">ROOT CAUSE FOUND</span>
                  <span className="ml-auto text-[11px] text-gray-400 font-medium">1m ago</span>
                </div>
                <div className="h-2 w-full bg-gray-100 rounded-full mb-6">
                  <div className="h-full bg-gray-200 rounded-full w-[65%]"></div>
                </div>
                <div className="bg-[#111] text-white rounded-lg py-3 px-4 flex justify-between items-center cursor-pointer hover:bg-black transition-colors">
                  <span className="text-sm font-semibold">Approve Patch</span>
                  <span className="bg-white/10 p-1 rounded">
                     <span className="text-[#ff6b00] text-sm">→</span>
                  </span>
                </div>
              </div>
              <h3 className="text-2xl font-bold font-serif mb-4 text-black">Share every step clearly</h3>
              <p className="text-gray-500 text-base leading-relaxed">
                Auto-generated RCA reports, timeline updates, and Slack notifications that your team (and CTO) actually understand.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-[#fafafa] rounded-3xl p-8 border border-gray-100 shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)] flex flex-col items-center text-center">
              <div className="w-full h-full min-h-[170px] relative mb-10 mt-2">
                <div className="absolute right-0 top-0 bg-[#ff6b00] text-white text-xs font-semibold px-4 py-3 rounded-2xl rounded-tr-sm max-w-[85%] text-left shadow-md">
                  Critical: Database CPU at 98%. App_lag alert scoring...
                </div>
                <div className="absolute left-0 top-16 bg-white border border-gray-100 text-gray-800 text-xs p-4 rounded-2xl rounded-tl-sm max-w-[90%] text-left shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
                  <div className="font-semibold text-gray-400 mb-1 text-[11px]">NeverDown Bot</div>
                  <div className="font-medium text-sm">New node provisioned. Traffic re-balancing successful.</div>
                </div>
              </div>
              <h3 className="text-2xl font-bold font-serif mb-4 text-black">Align on every next step</h3>
              <p className="text-gray-500 text-base leading-relaxed">
                Maintain full human-in-the-loop control. NeverDown proposes the fix; you decide if it goes live with one click.
              </p>
            </div>
          </div>
        </section>

        {/* Pipeline Section */}
        <section id="pipeline" className="mt-40">
          <div className="mb-20 max-w-2xl">
            <h2 className="text-4xl md:text-[3rem] font-serif font-bold text-black mb-6 leading-tight">
              The 5-Agent Remediation Pipeline
            </h2>
            <p className="text-gray-500 text-xl font-medium">
              Our proprietary multi-agent architecture ensures every incident is handled with extreme precision and safety protocols.
            </p>
          </div>

          <div className="relative">
            {/* Curving SVGs instead of pure squares */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 md:gap-6 relative z-10">
              {[
                { num: "01", title: "The Sanitizer", desc: "Filters noise and duplicates. Only real threats enter the pipe." },
                { num: "02", title: "The Detective", desc: "Scours logs, metrics, and traces to find the smoking gun." },
                { num: "03", title: "The Reasoner", desc: "Simulates potential fixes and evaluates safety impact." },
                { num: "04", title: "The Verifier", desc: "Tests the proposed patch in isolated environments." },
                { num: "05", title: "The Publisher", desc: "Deploys the fix and notifies the stakeholders via Slack." },
              ].map((step, i) => (
                <div key={i} className="relative group">
                  <div className="bg-white border border-gray-200 hover:border-gray-300 transition-all shadow-sm hover:shadow-md rounded-2xl p-6 h-full flex flex-col pt-8 duration-300 relative z-10">
                    <div className="flex items-center justify-between mb-8">
                      <span className="text-4xl font-serif text-[#ff6b00]/60 group-hover:text-[#ff6b00] transition-colors">{step.num}</span>
                    </div>
                    <h4 className="text-xl font-bold font-serif mb-3 text-black">{step.title}</h4>
                    <p className="text-gray-500 text-sm leading-relaxed">{step.desc}</p>
                  </div>
                  
                  {/* Animated Decorative Lines */}
                  {i < 4 && i % 2 === 0 && (
                    <div className="hidden md:block absolute border-gray-200 border-dashed z-0" 
                         style={{
                           left: '50%',
                           top: '50%',
                           bottom: '-40px', 
                           right: '-1.5rem',
                           borderLeftWidth: '2px',
                           borderBottomWidth: '2px',
                           borderRightWidth: '2px',
                           borderBottomLeftRadius: '24px',
                           borderBottomRightRadius: '24px',
                         }}>
                         <div className="absolute right-[-6px] top-[-6px] w-[10px] h-[10px] border-t-2 border-r-2 border-gray-300 transform rotate-[45deg] bg-white z-10"></div>
                         
                         <motion.div 
                           className="absolute w-2.5 h-2.5 bg-[#ff6b00] rounded-full shadow-[0_0_12px_4px_rgba(255,107,0,0.6)] z-20"
                           animate={{
                             top: ["0%", "100%", "100%", "0%"],
                             left: ["-5px", "-5px", "calc(100% - 5px)", "calc(100% - 5px)"],
                             opacity: [0, 1, 1, 1]
                           }}
                           transition={{
                             duration: 3,
                             repeat: Infinity,
                             ease: "linear",
                             times: [0, 0.4, 0.6, 1],
                             delay: i * 0.5
                           }}
                         />
                    </div>
                  )}

                  {i < 4 && i % 2 === 1 && (
                    <div className="hidden md:block absolute border-gray-200 border-dashed z-0" 
                         style={{
                           left: '50%',
                           bottom: '50%', 
                           top: '-40px', 
                           right: '-1.5rem',
                           borderLeftWidth: '2px',
                           borderTopWidth: '2px',
                           borderRightWidth: '2px',
                           borderTopLeftRadius: '24px',
                           borderTopRightRadius: '24px',
                         }}>
                         <div className="absolute right-[-6px] bottom-[-6px] w-[10px] h-[10px] border-t-2 border-r-2 border-gray-300 transform rotate-[45deg] bg-white z-10"></div>
                         
                         <motion.div 
                           className="absolute w-2.5 h-2.5 bg-[#ff6b00] rounded-full shadow-[0_0_12px_4px_rgba(255,107,0,0.6)] z-20"
                           animate={{
                             bottom: ["0%", "100%", "100%", "0%"],
                             left: ["-5px", "-5px", "calc(100% - 5px)", "calc(100% - 5px)"],
                             opacity: [0, 1, 1, 1]
                           }}
                           transition={{
                             duration: 3,
                             repeat: Infinity,
                             ease: "linear",
                             times: [0, 0.4, 0.6, 1],
                             delay: i * 0.5
                           }}
                         />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-20 px-6 md:px-12 mt-28 bg-[#fafafa]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between gap-16 md:gap-0">
          <div className="max-w-xs">
             <div className="font-bold text-2xl tracking-tight mb-6 text-black font-serif">NeverDown</div>
             <p className="text-gray-500 text-sm leading-relaxed mb-6 font-medium">
                The intelligent orchestration layer for the modern autonomous enterprise. Built in India.
             </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-12 md:gap-24">
             <div>
                <h5 className="text-[11px] font-bold text-black tracking-[0.15em] mb-6 uppercase">Product</h5>
                <ul className="space-y-4 text-sm text-gray-500 font-medium">
                   <li><Link href="#" className="hover:text-black transition-colors">Integrations</Link></li>
                   <li><Link href="#pipeline" className="hover:text-black transition-colors">Pipeline</Link></li>
                   <li><Link href="#" className="hover:text-black transition-colors">Pricing</Link></li>
                </ul>
             </div>
             <div>
                <h5 className="text-[11px] font-bold text-black tracking-[0.15em] mb-6 uppercase">Company</h5>
                <ul className="space-y-4 text-sm text-gray-500 font-medium">
                   <li><Link href="#" className="hover:text-black transition-colors">About</Link></li>
                   <li><Link href="#" className="hover:text-black transition-colors">Careers</Link></li>
                   <li><Link href="#" className="hover:text-black transition-colors">Contact</Link></li>
                </ul>
             </div>
             <div>
                <h5 className="text-[11px] font-bold text-black tracking-[0.15em] mb-6 uppercase">Legal</h5>
                <ul className="space-y-4 text-sm text-gray-500 font-medium">
                   <li><Link href="#" className="hover:text-black transition-colors">Privacy</Link></li>
                   <li><Link href="#" className="hover:text-black transition-colors">Terms</Link></li>
                   <li><Link href="#" className="hover:text-black transition-colors">Security</Link></li>
                </ul>
             </div>
          </div>
        </div>
        
        <div className="max-w-6xl mx-auto mt-20 pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center gap-6 text-xs text-gray-500 font-medium">
           <div>© 2024 NeverDown Inc. All rights reserved.</div>
           <div className="flex items-center gap-8">
              <Link href="#" className="hover:text-black transition-colors">Twitter</Link>
              <Link href="#" className="hover:text-black transition-colors">LinkedIn</Link>
              <Link href="#" className="hover:text-black transition-colors">GitHub</Link>
           </div>
        </div>
      </footer>
    </div>
  );
}
