"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Clock, CheckCircle, XCircle, Loader2, ExternalLink, AlertTriangle } from "lucide-react";
import PipelineVisualizer from "@/components/PipelineVisualizer";

const API_BASE = "http://localhost:8000/api/v1";

// Map backend status to agent index
const STATUS_TO_AGENT: Record<string, number> = {
  pending: -1,
  processing: 0,
  sanitizing: 0,
  analyzing: 1,
  reasoning: 2,
  verifying: 3,
  creating_pr: 4,
  pr_created: 4,
  completed: 5,
  failed: -2,
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Queued",
  processing: "Processing",
  sanitizing: "Sanitizing Code",
  analyzing: "Analyzing with Detective",
  reasoning: "Generating Fix with Reasoner",
  verifying: "Verifying in Sandbox",
  creating_pr: "Creating Pull Request",
  pr_created: "Pull Request Created!",
  completed: "Completed",
  failed: "Failed",
};

interface TimelineEvent {
  state: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

interface IncidentStatus {
  incident_id: string;
  status: string;
  current_state: string | null;
  timeline: TimelineEvent[];
  patches_generated: number;
  latest_patch_verified: boolean | null;
  pr_url: string | null;
  error_message: string | null;
}

export default function MonitorPage() {
  const params = useParams();
  const router = useRouter();
  const incidentId = params.id as string;

  const [status, setStatus] = useState<IncidentStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Fetch status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/incidents/${incidentId}/status`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch status: ${response.status}`);
      }

      const data: IncidentStatus = await response.json();
      setStatus(data);
      setError(null);

      // Stop polling if complete or failed
      if (data.status === "completed" || data.status === "pr_created" || data.status === "failed") {
        setIsPolling(false);
      }
    } catch (err) {
      console.error("Failed to fetch status:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch status");
    }
  }, [incidentId]);

  // Polling effect
  useEffect(() => {
    if (!isPolling) return;

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [isPolling, fetchStatus]);

  // Elapsed time counter
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const activeAgent = status ? STATUS_TO_AGENT[status.status] ?? -1 : -1;
  const failedAgent = status?.status === "failed" ? activeAgent : undefined;

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 blur-header h-16 flex items-center px-6 justify-between border-b border-border">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/")}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="font-bold text-lg">Live Pipeline Monitor</h1>
            <p className="text-xs text-gray-500 font-mono">Incident: {incidentId.slice(0, 8)}...</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Elapsed Time */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
            <Clock className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-mono text-blue-500">{formatTime(elapsedTime)}</span>
          </div>

          {/* Status Badge */}
          {status && (
            <div className={`
              flex items-center gap-2 px-3 py-1 rounded-full border
              ${status.status === "completed" || status.status === "pr_created" 
                ? "bg-green-500/10 border-green-500/20 text-green-500"
                : status.status === "failed"
                ? "bg-red-500/10 border-red-500/20 text-red-500"
                : "bg-primary/10 border-primary/20 text-primary"
              }
            `}>
              {status.status === "completed" || status.status === "pr_created" ? (
                <CheckCircle className="w-4 h-4" />
              ) : status.status === "failed" ? (
                <XCircle className="w-4 h-4" />
              ) : (
                <Loader2 className="w-4 h-4 animate-spin" />
              )}
              <span className="text-sm font-semibold">{STATUS_LABELS[status.status] || status.status}</span>
            </div>
          )}
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Pipeline Visualizer */}
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Agent Pipeline</h2>
            <div className="h-[600px] border border-border rounded-2xl bg-black/50 backdrop-blur-sm relative overflow-hidden">
              <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none" />
              <PipelineVisualizer 
                activeAgent={activeAgent}
                failedAgent={failedAgent}
              />
            </div>

            {/* PR Link */}
            {status?.pr_url && (
              <a
                href={status.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full px-6 py-4 bg-green-600 hover:bg-green-500 rounded-lg text-white font-semibold transition-all hover:ring-2 hover:ring-green-500/50"
              >
                <ExternalLink className="w-5 h-5" />
                View Generated Pull Request
              </a>
            )}
          </div>

          {/* Right: Live Logs */}
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Live Execution Logs</h2>
            
            {/* Error Message */}
            {(error || status?.error_message) && (
              <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{error || status?.error_message}</span>
              </div>
            )}

            {/* Timeline Logs */}
            <div className="rounded-lg border border-border overflow-hidden bg-black/50">
              <div className="flex items-center justify-between px-4 py-2 bg-border/50 border-b border-border">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/50" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                    <div className="w-3 h-3 rounded-full bg-green-500/50" />
                  </div>
                  <span className="text-xs font-mono text-gray-500 ml-2">
                    {isPolling ? (
                      <span className="flex items-center gap-2">
                        Live Output
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      </span>
                    ) : (
                      "Pipeline Complete"
                    )}
                  </span>
                </div>
              </div>

              <div className="p-4 h-[500px] overflow-y-auto font-mono text-xs space-y-1">
                {!status && (
                  <div className="text-gray-500 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Loading pipeline status...</span>
                  </div>
                )}
                
                {status?.timeline.map((event, idx) => {
                  const time = new Date(event.timestamp).toLocaleTimeString();
                  const agentName = event.state.includes("SANITIZ") ? "Sanitizer"
                    : event.state.includes("ANALYZ") || event.state.includes("DETECTIVE") ? "Detective"
                    : event.state.includes("REASON") ? "Reasoner"
                    : event.state.includes("VERIF") ? "Verifier"
                    : event.state.includes("PR") || event.state.includes("PUBLISH") ? "Publisher"
                    : "System";

                  return (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex gap-3"
                    >
                      <span className="text-gray-600">[{time}]</span>
                      <span className={`
                        ${agentName === "Sanitizer" ? "text-purple-400"
                        : agentName === "Detective" ? "text-indigo-400"
                        : agentName === "Reasoner" ? "text-purple-400"
                        : agentName === "Verifier" ? "text-indigo-400"
                        : agentName === "Publisher" ? "text-purple-400"
                        : "text-gray-400"}
                      `}>
                        {agentName}:
                      </span>
                      <span className="text-gray-300">
                        {event.state}
                        {event.details && ` - ${JSON.stringify(event.details)}`}
                      </span>
                    </motion.div>
                  );
                })}

                {isPolling && (
                  <div className="flex gap-1 mt-2">
                    <span className="text-primary">▊</span>
                    <span className="text-gray-600 animate-pulse">_</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
