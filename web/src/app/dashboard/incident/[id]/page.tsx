"use client";

import { Check, AlertCircle, ArrowRight, Activity, ArrowLeft, Send, CornerDownLeft, X } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import { getApiBase } from "@/lib/api";

const API_BASE = getApiBase();

export default function IncidentDetail() {
  const params = useParams();
  const id = params.id as string;
  const [incident, setIncident] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);

  // Feedback State
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  useEffect(() => {
    const fetchIncident = async () => {
      try {
        const res = await fetch(`${API_BASE}/incidents/${id.toLowerCase()}/details`);
        if (res.ok) {
          const data = await res.json();
          setIncident(data);
        }
      } catch (err) {
        console.error("Failed to fetch incident:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchIncident();
    const interval = setInterval(fetchIncident, 3000);
    return () => clearInterval(interval);
  }, [id]);

  const submitFeedback = async () => {
    if (!feedbackText.trim() || isSubmittingFeedback) return;
    setIsSubmittingFeedback(true);
    try {
      const res = await fetch(`${API_BASE}/incidents/${id.toLowerCase()}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decision: "request_changes",
          feedback_text: feedbackText
        })
      });
      if (res.ok) {
        setFeedbackText("");
        setIsFeedbackOpen(false);
        // Optimistically update status to refining
        setIncident((prev: any) => ({ ...prev, status: "refining" }));
      }
    } catch (err) {
      console.error("Feedback submission failed:", err);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  if (loading && !incident) {
     return <div className="min-h-screen flex items-center justify-center"><div className="w-6 h-6 rounded-full border-2 border-[#ff6b00] border-t-transparent animate-spin"></div></div>;
  }

  const title = incident?.title || "CI Failure detected";
  const statusStr = incident?.status || "processing";
  const isCompleted = ['resolved', 'completed', 'pr_created', 'awaiting_review'].includes(statusStr);
  const isFailed = statusStr === 'failed';

  const tabs = ["Detective Analysis", "AI Reasoning", "Patch Preview", "Verification"];

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
                <div className="text-[11px] font-bold text-gray-400 tracking-[0.15em] mb-3 uppercase">{id}</div>
                <h1 className="text-4xl font-serif font-bold text-black tracking-tight">{title}</h1>
             </div>
             <div className="flex items-center gap-2.5 bg-[#fff7ef] border border-[#ffdbbd] px-4 py-2 mt-4 rounded-full shadow-sm">
                {!isCompleted && !isFailed ? (
                  <div className="w-2 h-2 rounded-full bg-[#ff6b00] animate-[ping_2s_cubic-bezier(0,0,0.2,1)_infinite]"></div>
                ) : (
                  <div className={`w-2 h-2 rounded-full ${isCompleted ? 'bg-green-500' : 'bg-red-500'}`}></div>
                )}
                <span className={`text-[11px] font-extrabold tracking-[0.1em] uppercase ${isCompleted ? 'text-green-600' : isFailed ? 'text-red-600' : 'text-[#d97706]'}`}>
                  {isCompleted ? 'Completed' : isFailed ? 'Failed' : 'Active Analysis'}
                </span>
             </div>
          </div>

          {/* Stepper */}
          <div className="flex items-center justify-between bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-10">
             <StepItem title="Sanitizer" state={['pending', 'monitoring'].includes(statusStr) ? 'active' : 'completed'} />
             <StepDivider active={!['pending', 'monitoring'].includes(statusStr)} />
             <StepItem title="Detective" state={['pending', 'monitoring', 'sanitizing'].includes(statusStr) ? 'faded' : ['detecting'].includes(statusStr) ? 'active' : 'completed'} />
             <StepDivider active={!['pending', 'monitoring', 'sanitizing', 'detecting'].includes(statusStr)} faded={['pending', 'monitoring', 'sanitizing'].includes(statusStr)} />
             <StepItem title="Architect" state={['reasoning'].includes(statusStr) ? 'active' : ['verifying', 'creating_pr', 'pr_created', 'awaiting_review', 'resolved', 'completed'].includes(statusStr) ? 'completed' : 'faded'} />
             <StepDivider active={['creating_pr', 'pr_created', 'awaiting_review', 'resolved', 'completed'].includes(statusStr)} faded={!['creating_pr', 'pr_created', 'awaiting_review', 'resolved', 'completed'].includes(statusStr) && statusStr !== 'verifying'} />
             <StepItem title="Verifier" state={['verifying'].includes(statusStr) ? 'active' : ['creating_pr', 'pr_created', 'awaiting_review', 'resolved', 'completed'].includes(statusStr) ? 'completed' : 'faded'} />
             <StepDivider active={['pr_created', 'awaiting_review', 'resolved', 'completed'].includes(statusStr)} faded={!['pr_created', 'awaiting_review', 'resolved', 'completed'].includes(statusStr) && statusStr !== 'creating_pr'} />
             <StepItem title="Publisher" state={['creating_pr'].includes(statusStr) ? 'active' : ['pr_created', 'awaiting_review', 'resolved', 'completed'].includes(statusStr) ? 'completed' : 'faded'} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
             {/* Left pane: Tabs & Code */}
             <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
                <div className="flex border-b border-gray-100 px-2 pt-2">
                   {tabs.map((tab, i) => (
                       <button 
                          key={i} 
                          onClick={() => setActiveTab(i)}
                          className={`px-6 py-4 text-[13px] font-bold transition-colors ${activeTab === i ? "border-b-[3px] border-black text-black" : "text-gray-400 border-b-[3px] border-transparent hover:text-gray-600"}`}
                       >
                          {tab}
                       </button>
                    ))}
                </div>
                
                <div className="p-8 pb-10 flex-1">
                    {activeTab === 0 && (
                       <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                          <h3 className="text-lg font-serif font-bold text-black mb-4 tracking-tight">Failure Localization</h3>
                          <p className="text-[13px] text-gray-600 leading-relaxed mb-8 pr-12">
                             {incident?.detective_output?.failure_category ? `The Detective agent identified this as a ${incident.detective_output.failure_category.replace('_', ' ')}.` : "Analyzing the logs to determine the root cause of the failure and identify the affected module."}
                          </p>

                          <div className="bg-[#141414] rounded-xl border border-[#2a2a2a] overflow-hidden shadow-xl mb-10">
                             <div className="flex justify-between items-center px-4 py-3 border-b border-[#2a2a2a] bg-[#1a1a1a]">
                                <span className="text-[11px] text-gray-400 font-mono">Suspected Files</span>
                                <span className="text-[9px] font-bold tracking-widest text-[#ff6b00] uppercase">Analysis</span>
                             </div>
                             <div className="p-6 overflow-x-auto text-[13px] font-mono leading-relaxed">
                                {incident?.detective_output?.suspected_files?.length > 0 ? (
                                   <div className="space-y-4">
                                      {incident.detective_output.suspected_files.map((file: any, idx: number) => (
                                         <div key={idx} className="text-gray-300">
                                            <span className="text-blue-400">{file.path}</span>
                                            <span className="text-gray-500 ml-2">// Confidence: {(file.confidence * 100).toFixed(0)}%</span>
                                            {file.snippet && <pre className="mt-2 text-[11px] text-gray-500 bg-white/5 p-2 rounded">{file.snippet}</pre>}
                                         </div>
                                      ))}
                                   </div>
                                ) : (
                                   <pre className="text-gray-500">{'// Automated analysis details are being prepared...'}</pre>
                                )}
                             </div>
                          </div>
                       </motion.div>
                    )}

                    {activeTab === 1 && (
                       <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                          <h3 className="text-lg font-serif font-bold text-black mb-4 tracking-tight">AI Reasoning Path</h3>
                          <div className="bg-[#141414] rounded-xl border border-[#2a2a2a] overflow-hidden shadow-xl mb-10">
                             <div className="flex justify-between items-center px-4 py-3 border-b border-[#2a2a2a] bg-[#1a1a1a]">
                                <span className="text-[11px] text-gray-400 font-mono">Reasoner Plan</span>
                             </div>
                             <div className="p-6 text-[13px] font-mono leading-relaxed">
                                {incident?.reasoner_output ? (
                                   <div className="space-y-6">
                                      <div className="text-orange-400">// Root Cause Identified:</div>
                                      <div className="text-gray-300 pl-4">{incident.reasoner_output.root_cause}</div>
                                      <div className="text-blue-400 mt-4">// Proposed Fix Strategy:</div>
                                      <div className="text-gray-300 pl-4 leading-loose">{incident.reasoner_output.plan}</div>
                                   </div>
                                ) : (
                                   <pre className="text-gray-500">{'// Reasoner is formulating a repair strategy...'}</pre>
                                )}
                             </div>
                          </div>
                       </motion.div>
                    )}

                    {activeTab === 2 && (
                       <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                          <h3 className="text-lg font-serif font-bold text-black mb-4 tracking-tight">Patch Preview</h3>
                          <div className="bg-[#141414] rounded-xl border border-[#2a2a2a] overflow-hidden shadow-xl mb-10">
                             <div className="flex justify-between items-center px-4 py-3 border-b border-[#2a2a2a] bg-[#1a1a1a]">
                                <span className="text-[11px] text-gray-400 font-mono">Unified Diff</span>
                             </div>
                             <div className="p-6 overflow-x-auto text-[12px] font-mono leading-relaxed min-h-[300px]">
                                {incident?.patch_diff ? (
                                   <pre className="text-gray-300 whitespace-pre-wrap">
                                      {incident.patch_diff.split('\n').map((line: string, i: number) => {
                                         let color = "text-gray-400";
                                         if (line.startsWith('+')) color = "text-green-400 bg-green-900/20";
                                         if (line.startsWith('-')) color = "text-red-400 bg-red-900/20";
                                         if (line.startsWith('@@')) color = "text-blue-400";
                                         return <div key={i} className={color}>{line}</div>
                                      })}
                                   </pre>
                                ) : (
                                   <div className="flex flex-col items-center justify-center h-full text-gray-500 py-20">
                                      <Activity className="w-8 h-8 animate-pulse mb-4" />
                                      <span>Generating optimized patch...</span>
                                   </div>
                                )}
                             </div>
                          </div>
                       </motion.div>
                    )}

                    {activeTab === 3 && (
                       <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                          <h3 className="text-lg font-serif font-bold text-black mb-4 tracking-tight">Verification Results</h3>
                          <div className="grid grid-cols-2 gap-4 mb-6">
                             <div className="bg-white border border-gray-100 rounded-xl p-4">
                                <div className="text-[10px] uppercase text-gray-400 font-bold mb-1">Status</div>
                                <div className="flex items-center gap-2">
                                   <div className={`w-2 h-2 rounded-full ${incident?.verifier_output?.status === 'success' ? 'bg-green-500' : 'bg-orange-500'}`}></div>
                                   <span className="text-sm font-bold uppercase">{incident?.verifier_output?.status || "Waiting"}</span>
                                </div>
                             </div>
                             <div className="bg-white border border-gray-100 rounded-xl p-4">
                                <div className="text-[10px] uppercase text-gray-400 font-bold mb-1">Tests Passed</div>
                                <div className="text-sm font-bold">{incident?.verifier_output?.tests_passed ?? 0} total</div>
                             </div>
                          </div>
                          <div className="bg-[#141414] rounded-xl border border-[#2a2a2a] overflow-hidden shadow-xl">
                             <div className="flex justify-between items-center px-4 py-3 border-b border-[#2a2a2a] bg-[#1a1a1a]">
                                <span className="text-[11px] text-gray-400 font-mono">Sandbox Output</span>
                             </div>
                             <div className="p-6 overflow-x-auto text-[11px] font-mono leading-relaxed bg-black/50 text-gray-400 max-h-[400px] overflow-y-auto">
                                {incident?.verifier_output?.test_output ? (
                                   <pre className="whitespace-pre-wrap">{incident.verifier_output.test_output}</pre>
                                ) : (
                                   <pre className="text-gray-600">{'// Awaiting sandbox verification trace...'}</pre>
                                )}
                             </div>
                          </div>
                       </motion.div>
                    )}

                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-10 mb-4">Raw Execution Logs</div>
                    <div className="bg-[#141414] border border-[#2a2a2a] rounded-xl p-6 font-mono text-[11.5px] text-gray-300 leading-relaxed shadow-xl max-h-[300px] overflow-y-auto custom-scrollbar">
                       {incident?.logs ? <pre className="whitespace-pre-wrap">{incident.logs}</pre> : <div>Awaiting detailed execution trace...</div>}
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
                     {incident?.description || "A memory leak in the handshake pooler is causing the connection exhaustion observed during high-traffic spikes."}
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
                   <div className="space-y-6 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                      {incident?.timeline?.length > 0 ? (
                         [...incident.timeline].reverse().map((event: any, idx: number) => (
                            <div key={idx} className="flex gap-4">
                               <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                                  event.state === 'RECEIVED' ? 'bg-blue-50 text-blue-500' :
                                  event.state === 'RESOLVED' ? 'bg-green-50 text-green-500' :
                                  'bg-orange-50 text-orange-500'
                               }`}>
                                  {event.state === 'RECEIVED' ? <Activity className="w-4 h-4" /> :
                                   event.state === 'RESOLVED' ? <Check className="w-4 h-4" /> :
                                   <AlertCircle className="w-4 h-4" />}
                               </div>
                               <div>
                                  <div className="text-[12px] font-bold text-black">{event.state.replace('_', ' ')}</div>
                                  <div className="text-[11px] text-gray-500 mt-0.5 leading-relaxed">{event.details?.message || "Automated transition"}</div>
                                  <div className="text-[9px] font-medium text-gray-400 mt-1.5">
                                     {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                  </div>
                               </div>
                            </div>
                         ))
                      ) : (
                         <div className="text-xs text-gray-400 py-4 italic">No events recorded yet...</div>
                      )}
                   </div>
                   
                   <button className="w-full mt-6 py-3 rounded-xl border border-gray-200 text-xs font-bold text-gray-500 hover:bg-gray-50 hover:text-black transition-colors">
                      View All Logs
                   </button>
                </div>
             </div>
          </div>
       </div>

       {/* Floating Action Bar */}
       <div className="fixed bottom-0 left-64 right-0 p-6 pointer-events-none z-50 flex flex-col items-center justify-end pb-8">
          <AnimatePresence>
             {isFeedbackOpen && (
               <motion.div 
                 initial={{ opacity: 0, y: 20, scale: 0.95 }}
                 animate={{ opacity: 1, y: 0, scale: 1 }}
                 exit={{ opacity: 0, y: 10, scale: 0.95 }}
                 className="w-full max-w-[1200px] mb-4 pointer-events-auto"
               >
                 <div className="bg-white/80 backdrop-blur-xl border border-white/40 shadow-[0_8px_30px_rgb(0,0,0,0.12)] rounded-2xl p-4 flex flex-col gap-3 relative overflow-hidden">
                    {/* Glowing Accent */}
                    <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#ff6b00]/50 to-transparent"></div>
                    <div className="flex justify-between items-center px-1">
                       <span className="text-[11px] font-extrabold text-[#ff6b00] uppercase tracking-widest">Refine AI Fix</span>
                       <button onClick={() => setIsFeedbackOpen(false)} className="text-gray-400 hover:text-black transition-colors rounded-full p-1">
                          <X className="w-4 h-4" />
                       </button>
                    </div>
                    <div className="relative">
                       <textarea 
                          value={feedbackText}
                          onChange={(e) => setFeedbackText(e.target.value)}
                          placeholder="Instruct the Reasoner on what to change..."
                          autoFocus
                          disabled={isSubmittingFeedback}
                          className="w-full bg-white/50 border border-gray-200/60 rounded-xl p-4 pr-12 text-[13px] text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#ff6b00]/20 focus:border-[#ff6b00]/40 transition-all resize-none min-h-[80px] disabled:opacity-50"
                          onKeyDown={(e) => {
                             if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                submitFeedback();
                             }
                          }}
                       />
                       <button 
                          onClick={submitFeedback}
                          disabled={!feedbackText.trim() || isSubmittingFeedback}
                          className="absolute right-3 bottom-3 w-8 h-8 rounded-lg bg-[#ff6b00] text-white flex items-center justify-center shadow-lg hover:bg-[#e66000] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                       >
                          {isSubmittingFeedback ? (
                             <div className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin"></div>
                          ) : (
                             <Send className="w-3.5 h-3.5 -ml-0.5" />
                          )}
                       </button>
                    </div>
                    <div className="text-[9px] font-medium text-gray-400 px-2 flex items-center gap-1.5">
                       <CornerDownLeft className="w-2.5 h-2.5 opacity-50" /> <kbd className="font-mono px-1 py-0.5 bg-gray-100 rounded border border-gray-200">Enter</kbd> to submit
                    </div>
                 </div>
               </motion.div>
             )}
          </AnimatePresence>

          <div className="bg-white border border-gray-200 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.15)] rounded-[20px] p-3 pl-6 flex items-center justify-between w-full max-w-[1200px] pointer-events-auto transition-transform duration-500 animate-in slide-in-from-bottom-8">
             <div className="flex items-center gap-3 text-[13px]">
                <span className="text-gray-500">Suggested Action:</span>
                <span className="font-bold text-black">
                   {incident?.pr_url ? `Review and Merge PR in ${incident?.metadata?.repository?.name || 'Repository'}` : "Awaiting PR creation or automatic fix..."}
                </span>
             </div>
             <div className="flex gap-3">
                {incident?.pr_url ? (
                   <>
                      <button 
                         onClick={() => setIsFeedbackOpen(!isFeedbackOpen)}
                         className={`px-6 py-2.5 rounded-xl text-[13px] font-bold transition-colors border ${isFeedbackOpen ? 'bg-gray-100 text-black border-gray-200 shadow-inner' : 'text-gray-600 hover:bg-gray-100 border-transparent hover:border-gray-200'}`}
                      >
                         Request Changes
                      </button>
                      <a href={incident.pr_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-[13px] font-bold text-white bg-[#1a1a1a] hover:bg-black transition-colors shadow-lg">
                         View PR on GitHub
                         <ArrowRight className="w-4 h-4 text-[#ff6b00]" strokeWidth={3} />
                      </a>
                   </>
                ) : (
                   <button className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-[13px] font-bold text-white bg-gray-400 cursor-not-allowed transition-colors shadow-lg">
                      Approve & Deploy Fix
                      <ArrowRight className="w-4 h-4 text-gray-300" strokeWidth={3} />
                   </button>
                )}
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
