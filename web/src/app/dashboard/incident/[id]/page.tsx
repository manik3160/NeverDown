"use client";

import { Check, AlertCircle, ArrowRight, Activity, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";

export default function IncidentDetail() {
  const params = useParams();
  const id = params.id as string;

  return (
    <div className="bg-[#fafafa] min-h-screen p-10 font-sans text-gray-900 pb-32">
       {/* Breadcrumb / Nav */}
       <div className="max-w-[1200px] mx-auto relative">
          <Link href="/dashboard" className="inline-flex items-center gap-2 text-[10px] font-bold text-gray-400 hover:text-black uppercase tracking-widest mb-10 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </Link>

          {/* Header */}
          <div className="flex justify-between items-start mb-12">
             <div>
                <div className="text-[11px] font-bold text-gray-400 tracking-[0.15em] mb-3 uppercase">{id || "INCIDENT-A7F3B2C1"}</div>
                <h1 className="text-4xl font-serif font-bold text-black tracking-tight">CI Failure: Authentication API</h1>
             </div>
             <div className="flex items-center gap-2.5 bg-[#fff7ef] border border-[#ffdbbd] px-4 py-2 mt-4 rounded-full shadow-sm">
                <div className="w-2 h-2 rounded-full bg-[#ff6b00] animate-[ping_2s_cubic-bezier(0,0,0.2,1)_infinite]"></div>
                <span className="text-[11px] font-extrabold text-[#d97706] tracking-[0.1em] uppercase">Active Analysis</span>
             </div>
          </div>

          {/* Stepper */}
          <div className="flex items-center justify-between bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-10">
             <StepItem title="Sanitizer" state="completed" />
             <StepDivider />
             <StepItem title="Detective" state="completed" />
             <StepDivider active />
             <StepItem title="Architect" state="active" />
             <StepDivider faded />
             <StepItem title="Verifier" state="faded" />
             <StepDivider faded />
             <StepItem title="Publisher" state="faded" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
             {/* Left pane: Tabs & Code */}
             <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
                <div className="flex border-b border-gray-100 px-2 pt-2">
                   {["Detective Analysis", "AI Reasoning", "Patch Preview", "Verification"].map((tab, i) => (
                      <button key={i} className={`px-6 py-4 text-[13px] font-bold transition-colors ${i === 0 ? "border-b-[3px] border-black text-black" : "text-gray-400 border-b-[3px] border-transparent hover:text-gray-600"}`}>
                         {tab}
                      </button>
                   ))}
                </div>
                
                <div className="p-8 pb-10 flex-1">
                   <h3 className="text-lg font-serif font-bold text-black mb-4 tracking-tight">Failure Localization</h3>
                   <p className="text-[13px] text-gray-600 leading-relaxed mb-8 pr-12">
                      The failure was detected in the <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-[11px] font-mono border border-gray-200">auth-provider-v2.ts</code> module. A race condition occurs during the JWT validation handshake when multiple concurrent requests hit the caching layer before initialization.
                   </p>

                   <div className="bg-[#141414] rounded-xl border border-[#2a2a2a] overflow-hidden shadow-xl mb-10">
                      <div className="flex justify-between items-center px-4 py-3 border-b border-[#2a2a2a] bg-[#1a1a1a]">
                         <span className="text-[11px] text-gray-400 font-mono">src/services/auth-provider-v2.ts</span>
                         <span className="text-[9px] font-bold tracking-widest text-gray-500 uppercase">Typescript</span>
                      </div>
                      <div className="p-6 overflow-x-auto text-[13px] font-mono leading-relaxed">
<pre className="text-gray-300">
<span className="text-[#cba6f7]">async</span> <span className="text-[#89b4fa]">validateToken</span>(token: <span className="text-[#a6e3a1]">string</span>) {'{'}
  <span className="text-gray-500">// CRITICAL: This flag is not checked before cache access</span>
  <span className="text-[#cba6f7]">const</span> cached = <span className="text-[#cba6f7]">await</span> <span className="text-[#f38ba8]">this</span>.cache.<span className="text-[#89b4fa]">get</span>(token);

  <span className="text-[#cba6f7]">if</span> (!cached) {'{'}
<div className="bg-[#f38ba8]/10 w-[120%] -ml-6 px-6 py-0.5 border-l-[3px] border-[#f38ba8]">    <span className="text-[#cba6f7]">const</span> validated = <span className="text-[#cba6f7]">await</span> <span className="text-[#f38ba8]">this</span>.<span className="text-[#89b4fa]">handshake</span>(); <span className="text-[#f38ba8]">// Fails under load</span></div>
    <span className="text-[#cba6f7]">await</span> <span className="text-[#f38ba8]">this</span>.cache.<span className="text-[#89b4fa]">set</span>(token, validated);
    <span className="text-[#cba6f7]">return</span> validated;
  {'}'}

  <span className="text-[#cba6f7]">return</span> cached;
{'}'}
</pre>
                      </div>
                   </div>

                   <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">Raw Execution Logs</div>
                   <div className="bg-[#f9fafb] border border-gray-100 rounded-lg p-5 font-mono text-[11px] text-gray-400 leading-relaxed shadow-inner">
                      <div>[14:21:37] INF Initializing Auth Service...</div>
                      <div>[14:21:38] ERR Handshake timeout after 5000ms</div>
                      <div>[14:21:38] WRN Connection pool exhausted: 10/10 active</div>
                      <div>[14:21:39] FAT Trace: Process exit with code 1</div>
                   </div>
                </div>
             </div>

             {/* Right pane: Insight & Events */}
             <div className="lg:col-span-1 space-y-6">
                
                {/* Sentinel Insight */}
                <div className="bg-[#1c1c1c] rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
                   <div className="absolute -top-10 -right-10 w-40 h-40 bg-[#ff6b00]/10 rounded-full blur-[40px]"></div>
                   <h3 className="text-[11px] font-extrabold text-[#ff6b00] uppercase tracking-[0.15em] mb-4">NeverDown Insight</h3>
                   <p className="text-[15px] font-serif leading-relaxed mb-8 pr-4">
                     "A memory leak in the handshake pooler is causing the connection exhaustion observed during high-traffic spikes."
                   </p>
                   <div>
                      <div className="flex justify-between text-xs mb-3">
                         <span className="text-gray-400">Confidence Score</span>
                         <span className="text-[#ff6b00] font-bold">94%</span>
                      </div>
                      <div className="w-full bg-[#333] h-1.5 rounded-full overflow-hidden">
                         <motion.div initial={{ width: 0 }} animate={{ width: "94%" }} transition={{ duration: 1, ease: "easeOut" }} className="bg-gradient-to-r from-orange-400 to-[#ff6b00] h-full rounded-full"></motion.div>
                      </div>
                   </div>
                </div>

                {/* Related Events */}
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                   <h3 className="text-[14px] font-bold text-black mb-6 tracking-tight">Related Events</h3>
                   <div className="space-y-6">
                      
                      <div className="flex gap-4">
                         <div className="w-8 h-8 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center shrink-0">
                            <Activity className="w-4 h-4" />
                         </div>
                         <div>
                            <div className="text-[13px] font-bold text-black">New Deploy</div>
                            <div className="text-xs text-gray-500 mt-0.5 leading-relaxed">v2.4.0-rc1 triggered this spike</div>
                            <div className="text-[10px] font-medium text-gray-400 mt-1.5">2 hours ago</div>
                         </div>
                      </div>

                      <div className="flex gap-4">
                         <div className="w-8 h-8 rounded-full bg-orange-50 text-orange-500 flex items-center justify-center shrink-0">
                            <AlertCircle className="w-4 h-4" />
                         </div>
                         <div>
                            <div className="text-[13px] font-bold text-black">Error Spikes</div>
                            <div className="text-xs text-gray-500 mt-0.5 leading-relaxed">500 Errors increased by 400%</div>
                            <div className="text-[10px] font-medium text-gray-400 mt-1.5">1 hour ago</div>
                         </div>
                      </div>

                   </div>
                   
                   <button className="w-full mt-6 py-3 rounded-xl border border-gray-200 text-xs font-bold text-gray-500 hover:bg-gray-50 hover:text-black transition-colors">
                      View All Logs
                   </button>
                </div>
             </div>
          </div>
       </div>

       {/* Floating Action Bar */}
       <div className="fixed bottom-0 left-64 right-0 p-6 pointer-events-none z-50 flex justify-center pb-8 animate-in slide-in-from-bottom-8 duration-500">
          <div className="bg-white border border-gray-200 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.15)] rounded-[20px] p-3 pl-6 flex items-center justify-between w-full max-w-[1200px] pointer-events-auto">
             <div className="flex items-center gap-3 text-[13px]">
                <span className="text-gray-500">Suggested Action:</span>
                <span className="font-bold text-black">Rollback to v2.3.9 and apply Patch #441</span>
             </div>
             <div className="flex gap-3">
                <button className="px-6 py-2.5 rounded-xl text-[13px] font-bold text-gray-600 hover:bg-gray-100 transition-colors border border-transparent hover:border-gray-200">
                   Request Changes
                </button>
                <button className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-[13px] font-bold text-white bg-[#1a1a1a] hover:bg-black transition-colors shadow-lg">
                   Approve & Deploy Fix
                   <ArrowRight className="w-4 h-4 text-[#ff6b00]" strokeWidth={3} />
                </button>
             </div>
          </div>
       </div>
    </div>
  );
}

function StepItem({ title, state }: { title: string, state: "completed" | "active" | "faded" }) {
   if (state === "completed") {
      return (
         <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-black flex items-center justify-center text-white">
               <Check className="w-3.5 h-3.5" strokeWidth={3} />
            </div>
            <span className="text-sm font-bold text-black">{title}</span>
         </div>
      );
   }
   if (state === "active") {
      return (
         <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full border-2 border-[#ff6b00] flex items-center justify-center p-1">
               <div className="w-full h-full rounded-full border-2 border-[#ff6b00] animate-[spin_3s_linear_infinite] border-t-transparent"></div>
            </div>
            <span className="text-sm font-bold text-[#ff6b00]">{title}</span>
         </div>
      );
   }
   return (
      <div className="flex items-center gap-3 opacity-40">
         <div className="w-6 h-6 rounded-full border-2 border-gray-300 flex items-center justify-center text-[10px] font-bold text-gray-400">
            {title[0]}
         </div>
         <span className="text-[13px] font-bold text-gray-400">{title}</span>
      </div>
   );
}

function StepDivider({ active, faded }: { active?: boolean, faded?: boolean }) {
   if (faded) return <div className="h-[2px] flex-1 mx-6 bg-gray-100"></div>;
   if (active) return <div className="h-[3px] flex-1 mx-6 bg-gradient-to-r from-black to-[#ff6b00]"></div>;
   return <div className="h-[3px] flex-1 mx-6 bg-black"></div>;
}
