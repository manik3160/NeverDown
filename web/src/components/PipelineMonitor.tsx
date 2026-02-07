"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { CheckCircle, XCircle, Loader2, ExternalLink, Clock } from "lucide-react";

// Map backend status to agent index (0-4)
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

interface PipelineMonitorProps {
  incidentId: string;
  onActiveAgentChange: (agentIndex: number) => void;
  onLogsUpdate: (logs: string[]) => void;
  onComplete: (prUrl: string | null, error: string | null) => void;
}

export default function PipelineMonitor({
  incidentId,
  onActiveAgentChange,
  onLogsUpdate,
  onComplete,
}: PipelineMonitorProps) {
  const [status, setStatus] = useState<IncidentStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Poll for status updates
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/incidents/${incidentId}/status`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch status: ${response.status}`);
      }

      const data: IncidentStatus = await response.json();
      setStatus(data);

      // Update active agent based on status
      const agentIndex = STATUS_TO_AGENT[data.status] ?? -1;
      onActiveAgentChange(agentIndex);

      // Convert timeline to log messages
      const logs = data.timeline.map((event) => {
        const time = new Date(event.timestamp).toLocaleTimeString();
        return `[${time}] ${event.state}${event.details ? `: ${JSON.stringify(event.details)}` : ""}`;
      });
      onLogsUpdate(logs);

      // Check if complete
      if (data.status === "completed" || data.status === "pr_created") {
        setIsPolling(false);
        onComplete(data.pr_url, null);
      } else if (data.status === "failed") {
        setIsPolling(false);
        onComplete(null, data.error_message || "Pipeline failed");
      }
    } catch (error) {
      console.error("Failed to fetch status:", error);
    }
  }, [incidentId, onActiveAgentChange, onLogsUpdate, onComplete]);

  // Polling effect
  useEffect(() => {
    if (!isPolling) return;

    // Initial fetch
    fetchStatus();

    // Poll every 2 seconds
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

  const getStatusIcon = () => {
    if (!status) return <Loader2 className="w-5 h-5 animate-spin text-primary" />;
    
    switch (status.status) {
      case "completed":
      case "pr_created":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Loader2 className="w-5 h-5 animate-spin text-primary" />;
    }
  };

  const getStatusText = () => {
    if (!status) return "Initializing...";
    
    const statusMap: Record<string, string> = {
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
    
    return statusMap[status.status] || status.status;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-zinc-900/50 border border-border rounded-xl p-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <p className="font-semibold">{getStatusText()}</p>
            <p className="text-xs text-gray-500">
              Incident: {incidentId.slice(0, 8)}...
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Elapsed Time */}
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Clock className="w-4 h-4" />
            <span className="font-mono">{formatTime(elapsedTime)}</span>
          </div>

          {/* PR Link */}
          {status?.pr_url && (
            <a
              href={status.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg text-green-500 text-sm font-semibold hover:bg-green-500/20 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              View PR
            </a>
          )}
        </div>
      </div>

      {/* Error Message */}
      {status?.error_message && (
        <div className="mt-3 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          {status.error_message}
        </div>
      )}

      {/* Progress Indicators */}
      {status && status.status !== "failed" && (
        <div className="mt-4 flex items-center gap-2">
          {["Sanitizer", "Detective", "Reasoner", "Verifier", "Publisher"].map((agent, idx) => {
            const currentAgent = STATUS_TO_AGENT[status.status] ?? -1;
            const isComplete = currentAgent > idx || status.status === "completed" || status.status === "pr_created";
            const isActive = currentAgent === idx;

            return (
              <div
                key={agent}
                className={`
                  flex-1 h-1 rounded-full transition-all duration-300
                  ${isComplete ? "bg-green-500" : isActive ? "bg-primary animate-pulse" : "bg-border"}
                `}
              />
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
