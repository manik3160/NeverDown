"use client";

import { useState, useEffect, useRef } from "react";
import { 
  CheckCircle, 
  Circle, 
  Loader2, 
  Terminal, 
  Play, 
  Pause, 
  XOctagon, 
  ShieldCheck,
  ChevronDown,
  ChevronUp
} from "lucide-react";

import { getApiBase } from "@/lib/api";

const API_BASE = getApiBase();

interface Incident {
  id: string;
  title: string;
  status: string;
  created_at: string;
  timeline: any[];
}

export default function ActivePipelines() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [expandedTerminals, setExpandedTerminals] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const response = await fetch(`${API_BASE}/incidents`);
        const data = await response.json();
        const list = Array.isArray(data) ? data : [];
        // Filter for active incidents (not resolved/completed)
        const active = list.filter((i: Incident) => 
          i.status !== "resolved" && i.status !== "completed"
        );
        setIncidents(active);
      } catch (error) {
        console.error("Failed to fetch incidents:", error);
      }
    };

    fetchIncidents();
    const interval = setInterval(fetchIncidents, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, []);

  const toggleTerminal = (id: string) => {
    setExpandedTerminals(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Active Pipelines</h1>
        <div className="flex items-center gap-3">
           <button className="px-4 py-2 text-sm font-medium bg-[#1f2937] border border-[#374151] rounded-lg text-gray-300 hover:text-white transition-colors">
              Active View
           </button>
           <button className="px-4 py-2 text-sm font-medium bg-[#1f2937]/50 border border-[#374151]/50 rounded-lg text-gray-500 hover:text-gray-300 transition-colors">
              History Log
           </button>
           <button className="px-4 py-2 text-sm font-medium bg-[#1f2937]/50 border border-[#374151]/50 rounded-lg text-gray-500 hover:text-gray-300 transition-colors">
              Configuration
           </button>
           <div className="ml-4 flex items-center gap-2 px-3 py-1.5 rounded bg-blue-900/20 border border-blue-900/50 text-blue-400 text-xs font-bold">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
              SYSTEM: NOMINAL
           </div>
           <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-yellow-900/20 border border-yellow-900/50 text-yellow-500 text-xs font-bold">
              <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
              Active Agents: {incidents.length > 0 ? incidents.length * 2 : 0}
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {incidents.length === 0 ? (
           <div className="col-span-full py-20 text-center text-gray-500 border border-dashed border-[#374151] rounded-xl">
              No active pipelines running. Trigger a manual incident from the dashboard.
           </div>
        ) : (
           incidents.map((incident) => (
             <PipelineCard 
               key={incident.id} 
               incident={incident} 
               isTerminalExpanded={!!expandedTerminals[incident.id]}
               onToggleTerminal={() => toggleTerminal(incident.id)}
             />
           ))
        )}
      </div>
    </div>
  );
}

function PipelineCard({ incident, isTerminalExpanded, onToggleTerminal }: { 
  incident: Incident, 
  isTerminalExpanded: boolean, 
  onToggleTerminal: () => void 
}) {
  const steps = [
    { id: "detection", label: "DETECTION", status: "completed" },
    { id: "diagnostics", label: "DIAGNOSTICS", status: "completed" },
    { id: "patch_gen", label: "PATCH GEN", status: "processing" },
    { id: "testing", label: "TESTING", status: "pending" },
    { id: "deploy", label: "DEPLOY", status: "pending" },
  ];

  // Map actual status to step progress (simplified logic for demo)
  const currentStatus = incident.status.toLowerCase();
  
  // Logic to determine step status based on incident status
  const getStepStatus = (stepId: string) => {
     if (currentStatus === "pending") return stepId === "detection" ? "processing" : "pending";
     if (currentStatus === "analyzing") return stepId === "diagnostics" ? "processing" : (stepId === "detection" ? "completed" : "pending");
     if (currentStatus === "reasoning") return stepId === "patch_gen" ? "processing" : (["detection", "diagnostics"].includes(stepId) ? "completed" : "pending");
     if (currentStatus === "verifying") return stepId === "testing" ? "processing" : (["detection", "diagnostics", "patch_gen"].includes(stepId) ? "completed" : "pending");
     if (currentStatus === "creating_pr" || currentStatus === "awaiting_review") return "completed";
     return "pending";
  }

  return (
    <div className="bg-[#0a0a0b] border border-[#1f2937] rounded-xl p-6 shadow-xl">
      {/* Card Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
           <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold text-white tracking-wide uppercase">
                 {incident.title.length > 30 ? incident.title.substring(0, 30) + "..." : incident.title}
              </h3>
           </div>
           <div className="text-xs font-mono text-gray-500">ID: {incident.id.substring(0, 8).toUpperCase()}</div>
        </div>
        <button className="text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2">View Full Details</button>
      </div>

      {/* Steps List */}
      <div className="space-y-3 mb-8">
        {steps.map((step, index) => {
           const status = getStepStatus(step.id);
           return (
              <div key={step.id} className="flex items-center justify-between p-3 rounded bg-[#111827] border border-[#1f2937]/50">
                 <div className="flex items-center gap-4">
                    <span className="text-xs font-mono text-gray-600">0{index + 1}</span>
                    <span className={`font-medium tracking-wide ${
                       status === "processing" ? "text-white" : 
                       status === "completed" ? "text-gray-300" : "text-gray-600"
                    }`}>
                       {step.label}
                    </span>
                 </div>
                 <div>
                    {status === "completed" && <CheckCircle className="w-5 h-5 text-green-500" />}
                    {status === "processing" && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
                    {status === "pending" && <Circle className="w-5 h-5 text-gray-700" />}
                 </div>
              </div>
           );
        })}
      </div>

      {/* Terminal View */}
      <div className="border border-[#1f2937] rounded-lg overflow-hidden bg-[#0a0a0b]">
        <div 
          className="flex items-center justify-between px-4 py-2 bg-[#111827] border-b border-[#1f2937] cursor-pointer hover:bg-[#1f2937]/80"
          onClick={onToggleTerminal}
        >
           <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-gray-400" />
              <span className="text-xs font-mono text-gray-400">agent-log-stream.sh</span>
           </div>
           <div className="flex items-center gap-2">
              <div className="flex gap-1.5">
                 <div className="w-2 h-2 rounded-full bg-red-500/20"></div>
                 <div className="w-2 h-2 rounded-full bg-yellow-500/20"></div>
              </div>
              {isTerminalExpanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
           </div>
        </div>
        
        {isTerminalExpanded && (
           <div className="p-4 font-mono text-xs text-gray-400 h-48 overflow-y-auto space-y-1 bg-black/50">
              <div className="text-green-500/50">$ initiating autonomous_agent --mode=reasoner</div>
              {(incident.timeline || []).slice().reverse().map((event: any, i: number) => (
                 <div key={i} className="flex gap-2">
                    <span className="text-blue-500/50">[{new Date(event.timestamp).toLocaleTimeString()}]</span>
                    <span>{event.state}: {JSON.stringify(event.details || event.message || "")}</span>
                 </div>
              ))}
              <div className="animate-pulse text-blue-500">_</div>
           </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-4 gap-3 mt-6">
         <button className="py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-colors">
            Pause
         </button>
         <button className="py-2 rounded bg-transparent border border-red-500/50 text-red-500 hover:bg-red-950/30 text-xs font-bold transition-colors">
            Abort
         </button>
         <button className="col-span-2 py-2 rounded bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition-colors flex items-center justify-center gap-2">
            Authorize Deploy
         </button>
      </div>
    </div>
  );
}
