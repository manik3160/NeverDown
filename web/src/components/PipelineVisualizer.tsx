"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Shield, Search, Brain, Stethoscope, GitPullRequest, CheckCircle, XCircle } from "lucide-react";

const agents = [
  {
    id: 0,
    name: "Sanitizer",
    icon: Shield,
    color: "#9333FF",
    responsibilities: "Secret detection & redaction. Scans codebase for API keys, tokens, and credentials.",
  },
  {
    id: 1,
    name: "Detective",
    icon: Search,
    color: "#6366F1",
    responsibilities: "Error detection & analysis. Identifies runtime errors, stack traces, and failure patterns.",
  },
  {
    id: 2,
    name: "Reasoner",
    icon: Brain,
    color: "#9333FF",
    responsibilities: "Root cause analysis & fix generation. Uses LLM to propose code fixes with high confidence.",
  },
  {
    id: 3,
    name: "Verifier",
    icon: Stethoscope,
    color: "#6366F1",
    responsibilities: "Sandbox testing & validation. Applies patches in isolated Docker environment and runs tests.",
  },
  {
    id: 4,
    name: "Publisher",
    icon: GitPullRequest,
    color: "#9333FF",
    responsibilities: "Pull request creation. Generates PR with detailed description and pushes to GitHub for review.",
  },
];

interface PipelineVisualizerProps {
  activeAgent?: number; // -1 = none, 0-4 = agent index, 5 = all complete
  completedAgents?: number[]; // Array of completed agent indices
  failedAgent?: number; // Index of failed agent, if any
}

export default function PipelineVisualizer({
  activeAgent = -1,
  completedAgents = [],
  failedAgent,
}: PipelineVisualizerProps) {
  const [hoveredAgent, setHoveredAgent] = useState<number | null>(null);

  const getAgentStatus = (agentId: number) => {
    if (failedAgent === agentId) return "failed";
    if (activeAgent === 5 || completedAgents.includes(agentId)) return "complete";
    if (activeAgent === agentId) return "active";
    if (activeAgent > agentId) return "complete";
    return "pending";
  };

  return (
    <div className="relative h-full flex flex-col items-center justify-center py-12">
      <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
        {agents.slice(0, -1).map((_, idx) => {
          const isActive = activeAgent >= idx;
          return (
            <line
              key={idx}
              x1="50%"
              y1={`${((idx + 1) / (agents.length + 1)) * 100}%`}
              x2="50%"
              y2={`${((idx + 2) / (agents.length + 1)) * 100}%`}
              stroke={isActive ? "rgba(147, 51, 255, 0.6)" : "rgba(147, 51, 255, 0.2)"}
              strokeWidth="2"
              strokeDasharray="8 4"
              className={isActive ? "animate-marching-ants" : ""}
              style={{
                animationDelay: `${idx * 0.2}s`,
              }}
            />
          );
        })}
      </svg>

      <div className="relative z-10 space-y-6 w-full max-w-md">
        {agents.map((agent, idx) => {
          const Icon = agent.icon;
          const isHovered = hoveredAgent === agent.id;
          const status = getAgentStatus(agent.id);

          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              onHoverStart={() => setHoveredAgent(agent.id)}
              onHoverEnd={() => setHoveredAgent(null)}
              className="relative group cursor-pointer"
            >
              <div
                className={`
                  flex items-center gap-4 p-4 rounded-lg border transition-all duration-300
                  ${status === "active" ? "border-primary bg-primary/10 ring-2 ring-primary/50 scale-[1.02]" : ""}
                  ${status === "complete" ? "border-green-500/50 bg-green-500/5" : ""}
                  ${status === "failed" ? "border-red-500/50 bg-red-500/5" : ""}
                  ${status === "pending" ? "border-border bg-background/50 opacity-50" : ""}
                  ${isHovered && status !== "active" ? "border-primary bg-primary/5" : ""}
                  hover:ring-2 hover:ring-primary/50
                `}
              >
                <div
                  className={`
                    w-12 h-12 rounded-lg flex items-center justify-center border relative
                    ${status === "active" ? "border-primary" : "border-border"}
                  `}
                  style={{ backgroundColor: `${agent.color}15` }}
                >
                  <Icon className="w-6 h-6" style={{ color: agent.color }} />
                  
                  {/* Status indicator overlay */}
                  {status === "complete" && (
                    <div className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-3 h-3 text-white" />
                    </div>
                  )}
                  {status === "failed" && (
                    <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                      <XCircle className="w-3 h-3 text-white" />
                    </div>
                  )}
                  {status === "active" && (
                    <div className="absolute -top-1 -right-1 w-5 h-5 bg-primary rounded-full flex items-center justify-center">
                      <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                    </div>
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-gray-500">AGENT {agent.id}</span>
                    {status === "active" && (
                      <div className="h-1 w-1 rounded-full bg-primary animate-pulse" />
                    )}
                  </div>
                  <h3 className="text-lg font-semibold tracking-tight">{agent.name}</h3>
                </div>

                <div className="text-xs font-mono text-gray-600">{String(idx + 1).padStart(2, "0")}</div>
              </div>

              {/* Tooltip */}
              {isHovered && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="absolute left-full ml-4 top-1/2 -translate-y-1/2 w-72 p-4 rounded-lg border border-primary bg-background shadow-2xl z-50"
                >
                  <div className="text-xs font-mono text-primary mb-2">RESPONSIBILITIES</div>
                  <p className="text-sm text-gray-300 leading-relaxed">{agent.responsibilities}</p>
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 w-2 h-2 rotate-45 bg-background border-l border-b border-primary" />
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
