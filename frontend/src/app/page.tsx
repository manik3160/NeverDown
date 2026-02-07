'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { 
  ArrowRight, 
  ShieldAlert, 
  Zap, 
  Github, 
  Cpu, 
  Terminal, 
  History,
  Activity,
  CheckCircle2,
  Lock,
  Globe,
  Server,
  Fingerprint,
  Search,
  Brain,
  Database,
  Key,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  MessageSquare,
  BarChart3,
  Layers,
  ZapOff
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import { useRef, useState, useEffect } from 'react';
import { ProfessionalHeroAnimation } from '@/components/landing/ProfessionalHeroAnimation';
import { SmoothScroll } from '@/components/landing/SmoothScroll';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

export default function LandingPage() {
  const [activeFaq, setActiveFaq] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    
    // Reveal animations on scroll
    const sections = gsap.utils.toArray('.reveal-section');
    sections.forEach((section: any) => {
      gsap.fromTo(section, 
        { opacity: 0, y: 30 },
        { 
          opacity: 1, 
          y: 0, 
          duration: 1.2, 
          ease: "power3.out",
          scrollTrigger: {
            trigger: section,
            start: "top 85%",
            toggleActions: "play none none none"
          }
        }
      );
    });
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    const lenis = (window as any).lenis;
    if (el && lenis) {
      lenis.scrollTo(el, {
        offset: -100,
        duration: 2,
      });
    } else if (el) {
      window.scrollTo({
        top: el.offsetTop - 100,
        behavior: 'smooth'
      });
    }
  };

  const pricingPlans = [
    {
      name: "Standard",
      price: "$0",
      desc: "For small teams starting with autonomy.",
      features: ["3 Managed Repositories", "Standard Analysis Velocity", "Public PR Publishing", "Discord Community Support", "14-day Log Retention"],
      cta: "Get Started",
      highlight: false
    },
    {
      name: "Premium",
      price: "$99",
      period: "/mo",
      desc: "Total autonomy for mission-critical apps.",
      features: ["Unlimited Repositories", "Priority Agent Provisioning", "Private PR Security", "On-Demand Sandbox Verdicts", "90-day Advanced Analytics", "Dedicated Slack Support"],
      cta: "Start Free Trial",
      highlight: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      desc: "Compliance and hyperscale reliability.",
      features: ["Custom Agent Behaviors", "On-Prem / Private VPC", "SOC2 Compliance Integration", "24/7 Phone Support", "SLA Performance Liability", "Unlimited History Data"],
      cta: "Contact Sales",
      highlight: false
    }
  ];

  return (
    <SmoothScroll>
      <div ref={containerRef} className="bg-[#050505] text-[#FAFAFA] selection:bg-cyan-500/30 overflow-x-hidden font-sans antialiased">
        {/* NAVIGATION */}
        <nav className="fixed top-0 left-0 right-0 z-[100] border-b border-white/[0.04] bg-[#050505]/80 backdrop-blur-md">
          <div className="container mx-auto px-6 h-20 flex justify-between items-center">
            <Link href="/" className="flex items-center gap-2.5 font-semibold text-lg tracking-tight group">
              <div className="w-8 h-8 bg-white text-black rounded-lg flex items-center justify-center transition-transform group-hover:scale-95">
                <Zap className="w-4 h-4 fill-current" />
              </div>
              <span className="tracking-tight">NeverDown</span>
            </Link>
            
            <div className="hidden lg:flex gap-10 items-center">
            {['Technology', 'Security', 'Pricing'].map((item) => (
              <button 
                key={item} 
                onClick={() => scrollTo(item.toLowerCase())}
                className="text-[13px] font-medium text-white/50 hover:text-white transition-colors tracking-wide cursor-pointer"
              >
                {item}
              </button>
            ))}
            <div className="h-4 w-px bg-white/10" />
              <Link href="/login" className="text-[13px] font-medium text-white/50 hover:text-white transition-colors">Sign In</Link>
              <Button asChild size="sm" className="bg-white text-black hover:bg-white/90 rounded-full px-6 font-semibold h-10 shadow-lg shadow-white/5">
                <Link href="/dashboard">Launch Console</Link>
              </Button>
            </div>
          </div>
        </nav>

        {/* HERO SECTION */}
        <section className="relative min-h-screen flex items-center pt-20">
          <ProfessionalHeroAnimation />
          
          <div className="container mx-auto px-6 relative z-10 grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
              <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 1 }}
                  className="space-y-12"
              >
                  <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] text-white/70 text-[11px] font-medium tracking-wide">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
                      Distributed Infrastructure Intelligence
                  </div>
                  
                  <div className="space-y-6">
                    <h1 className="text-6xl md:text-8xl font-medium tracking-tight leading-[0.9] text-white">
                        Your code <br />
                        <span className="text-white/40 italic">heals itself.</span>
                    </h1>
                    <p className="text-lg md:text-xl text-white/50 max-w-xl leading-relaxed font-normal">
                        The premier autonomous reliability layer for mission-critical engineering swarms. 
                        Detect, analyze, and repair failures in real-time.
                    </p>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-5 pt-4">
                      <Button asChild size="lg" className="h-14 px-10 text-base bg-white text-black hover:bg-neutral-200 rounded-full font-semibold transition-all group shadow-2xl shadow-white/10">
                          <Link href="/dashboard" className="flex items-center">
                              Get Started <ArrowRight className="ml-2 w-4 h-4 transition-transform group-hover:translate-x-1" />
                          </Link>
                      </Button>
                      <Button asChild variant="ghost" size="lg" className="h-14 px-10 text-base text-white/70 hover:text-white hover:bg-white/5 rounded-full font-medium group border border-white/5">
                          <Link href="https://github.com" target="_blank" className="flex items-center">
                              <Github className="mr-2.5 w-5 h-5" /> GitHub
                          </Link>
                      </Button>
                  </div>
              </motion.div>
          </div>
        </section>

        {/* THE PROBLEM */}
        <section id="technology" className="py-44 container mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-32 items-center reveal-section">
            <div className="space-y-10">
                <Badge variant="outline" className="border-cyan-500/30 text-cyan-400 bg-cyan-500/5 px-4 py-1.5 rounded-full text-xs font-medium uppercase tracking-widest">The Problem</Badge>
                <h2 className="text-5xl md:text-6xl font-medium tracking-tight leading-[1.1]">
                  Downtime is <br />
                  <span className="text-white/30 italic">an expensive relic.</span>
                </h2>
                <p className="text-xl text-white/50 font-normal leading-relaxed max-w-lg">
                  Traditional observability only alerts you. NeverDown reasons over logs and cross-references 
                  your VCS history to provide a verified path to resolution within seconds.
                </p>
                
                <div className="grid grid-cols-1 gap-4 pt-4">
                    {[
                      { title: "Manual Intervention", value: "85% reduction", icon: ZapOff },
                      { title: "Mean Time to Fix", value: "Under 45s", icon: Layers }
                    ].map(stat => (
                      <div key={stat.title} className="flex items-center gap-6 p-6 bg-white/[0.02] border border-white/[0.05] rounded-[2rem] hover:bg-white/[0.04] transition-colors">
                        <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center">
                          <stat.icon className="w-5 h-5 text-white/60" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white/40 mb-1">{stat.title}</p>
                          <p className="text-2xl font-semibold tracking-tight">{stat.value}</p>
                        </div>
                      </div>
                    ))}
                </div>
            </div>
            <div className="relative aspect-square rounded-[3rem] overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/10 via-purple-500/5 to-transparent blur-3xl opacity-50 group-hover:opacity-100 transition-opacity duration-1000" />
                <div className="absolute inset-0 border border-white/5 rounded-[3rem] bg-white/[0.02] backdrop-blur-3xl flex items-center justify-center">
                    <BarChart3 className="w-24 h-24 text-white/10 transition-transform group-hover:scale-110 duration-1000" />
                </div>
            </div>
        </section>

        {/* CORE ENGINE */}
        <section id="security" className="py-44 bg-white/[0.02] reveal-section">
            <div className="container mx-auto px-6">
               <div className="max-w-3xl mb-32 space-y-6 text-center mx-auto">
                  <Badge variant="outline" className="border-white/10 text-white/40 bg-white/5 px-4 py-1.5 rounded-full text-xs font-medium uppercase tracking-widest">Agent Swarm</Badge>
                  <h2 className="text-5xl md:text-6xl font-medium tracking-tight">The Autonomous Pipeline.</h2>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                  {[
                      { title: "Sanitizer", icon: ShieldAlert, color: "text-emerald-400" },
                      { title: "Detective", icon: Search, color: "text-blue-400" },
                      { title: "Reasoner", icon: Brain, color: "text-purple-400" },
                      { title: "Verifier", icon: CheckCircle2, color: "text-cyan-400" }
                  ].map((agent, i) => (
                      <div 
                          key={agent.title}
                          className="bg-[#0A0A0A] p-10 rounded-[2.5rem] border border-white/[0.05] space-y-8 hover:border-white/10 transition-colors group"
                      >
                          <div className={`w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center ${agent.color} group-hover:scale-110 transition-transform`}>
                              <agent.icon className="w-6 h-6" />
                          </div>
                          <div className="space-y-3">
                            <h3 className="text-xl font-semibold tracking-tight">Agent {i}: {agent.title}</h3>
                            <p className="text-[15px] text-white/40 leading-relaxed font-normal">
                              {i === 0 && "Strips secrets and PII from logs locally."}
                              {i === 1 && "Finds error origin and identifies failure commit."}
                              {i === 2 && "Generates verified patch based on project context."}
                              {i === 3 && "Verifies fixes in isolated, ephemeral sandboxes."}
                            </p>
                          </div>
                      </div>
                  ))}
               </div>
            </div>
        </section>

        {/* PRICING */}
        <section id="pricing" className="py-44 container mx-auto px-6 reveal-section">
            <div className="text-center mb-32 space-y-6">
                <h2 className="text-5xl md:text-6xl font-medium tracking-tight">Simple Pricing.</h2>
                <p className="text-xl text-white/40 font-normal">Transparent tiers for every scale of infrastructure.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                {pricingPlans.map((plan) => (
                    <div key={plan.name} className={`p-12 rounded-[3.5rem] border ${plan.highlight ? 'border-white/10 bg-white/[0.02]' : 'border-white/5 bg-transparent'} flex flex-col justify-between group transition-all`}>
                        <div className="space-y-12">
                            <div className="space-y-4">
                                <h3 className="text-2xl font-semibold tracking-tight">{plan.name}</h3>
                                <p className="text-sm text-white/40 leading-relaxed font-normal">{plan.desc}</p>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-6xl font-medium tracking-tight">{plan.price}</span>
                                {plan.period && <span className="text-white/40 text-sm font-medium">{plan.period}</span>}
                            </div>
                            <ul className="space-y-4">
                                {plan.features.map(f => (
                                    <li key={f} className="flex gap-4 text-sm text-white/60 font-medium tracking-tight">
                                        <CheckCircle2 className="w-5 h-5 text-white/20 shrink-0" />
                                        {f}
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <Button asChild size="lg" className={`w-full mt-16 rounded-full font-semibold text-sm h-14 ${plan.highlight ? 'bg-white text-black hover:bg-neutral-200' : 'bg-white/5 text-white hover:bg-white/10 border border-white/5'}`}>
                            <Link href="/login">{plan.cta}</Link>
                        </Button>
                    </div>
                ))}
            </div>
        </section>

        {/* FOOTER */}
        <footer className="py-32 border-t border-white/[0.04] reveal-section">
          <div className="container mx-auto px-6">
              <div className="flex flex-col md:flex-row justify-between items-start gap-20">
                  <div className="max-w-sm space-y-8">
                      <Link href="/" className="flex items-center gap-2.5 font-semibold text-lg tracking-tight">
                        <div className="w-8 h-8 bg-white text-black rounded-lg flex items-center justify-center">
                          <Zap className="w-4 h-4 fill-current" />
                        </div>
                        <span>NeverDown</span>
                      </Link>
                      <p className="text-sm text-white/40 leading-relaxed font-normal">
                        The autonomous infrastructure mesh. Built for critical engineering teams 
                        at any stage of growth.
                      </p>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-24">
                    <div className="space-y-6">
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">Product</p>
                      <ul className="space-y-4 text-sm text-white/40 font-medium font-normal">
                        <li><a href="#" className="hover:text-white transition-colors">Agents</a></li>
                        <li><a href="#" className="hover:text-white transition-colors">Sandboxes</a></li>
                        <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                      </ul>
                    </div>
                    <div className="space-y-6">
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">Company</p>
                      <ul className="space-y-4 text-sm text-white/40 font-medium font-normal">
                        <li><a href="#" className="hover:text-white transition-colors">Changelog</a></li>
                        <li><a href="#" className="hover:text-white transition-colors">Docs</a></li>
                        <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                      </ul>
                    </div>
                  </div>
              </div>
              
              <div className="mt-40 pt-10 border-t border-white/[0.04] flex flex-col md:flex-row justify-between items-center gap-10 text-[13px] text-white/30 font-medium">
                  <div>&copy; {new Date().getFullYear()} NeverDown Autonomous Clusters.</div>
                  <div className="flex gap-10">
                      <a href="#" className="hover:text-white transition-colors leading-none pr-1">Twitter</a>
                      <a href="#" className="hover:text-white transition-colors leading-none pr-1">LinkedIn</a>
                      <a href="#" className="hover:text-white transition-colors leading-none">GitHub</a>
                  </div>
              </div>
          </div>
        </footer>
      </div>
    </SmoothScroll>
  );
}
