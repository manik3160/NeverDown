"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Copy, Check, Terminal } from "lucide-react";

interface LogEntry {
  timestamp: string;
  agent: string;
  level: string;
  message: string;
}

const mockLogs: LogEntry[] = [
  { timestamp: "00:00:01", agent: "Detective", level: "INFO", message: "Scanning repository for errors..." },
  { timestamp: "00:00:02", agent: "Detective", level: "INFO", message: "Found 2 errors in backend/index.js" },
  { timestamp: "00:00:03", agent: "Detective", level: "WARN", message: "ReferenceError: PORT is not defined" },
  { timestamp: "00:00:04", agent: "Reasoner", level: "INFO", message: "Analyzing root cause..." },
  { timestamp: "00:00:05", agent: "Reasoner", level: "REDACT", message: "Detected secret: GITHUB_TOKEN=<REDACTED>" },
  { timestamp: "00:00:06", agent: "Reasoner", level: "INFO", message: "Generating fix with 95% confidence..." },
  { timestamp: "00:00:07", agent: "Reasoner", level: "SUCCESS", message: "Patch generated successfully" },
];

const defaultDiff = `--- a/backend/index.js
+++ b/backend/index.js
@@ -1,7 +1,8 @@
+const PORT = process.env.PORT || 3000;
+
 const express = require('express');
 const app = express();
 
-app.listen(PORT, () => {
+app.listen(PORT, () => {
   console.log(\`Server running on port \${PORT}\`);
 });`;

interface AgentTerminalProps {
  logs?: string[]; // Real-time logs from pipeline
  diff?: string; // Generated diff from reasoner
  isLive?: boolean; // Whether we're showing live data
}

export default function AgentTerminal({ logs: liveLogs, diff, isLive = false }: AgentTerminalProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [copied, setCopied] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Handle mock logs when not live
  useEffect(() => {
    if (isLive) return;
    
    mockLogs.forEach((log, idx) => {
      setTimeout(() => {
        setLogs((prev) => [...prev, log]);
      }, idx * 800);
    });
  }, [isLive]);

  // Handle live logs
  useEffect(() => {
    if (!liveLogs || !isLive) return;

    const parsedLogs: LogEntry[] = liveLogs.map((log) => {
      // Parse log format: [time] STATE: details
      const match = log.match(/\[([^\]]+)\]\s+(\w+)(?::\s*(.*))?/);
      if (match) {
        const [, timestamp, state, details] = match;
        return {
          timestamp,
          agent: state.includes("SANITIZ") ? "Sanitizer" 
               : state.includes("ANALYZ") ? "Detective"
               : state.includes("REASON") ? "Reasoner"
               : state.includes("VERIF") ? "Verifier"
               : state.includes("PR") ? "Publisher"
               : "System",
          level: "INFO",
          message: details || state,
        };
      }
      return {
        timestamp: new Date().toLocaleTimeString(),
        agent: "System",
        level: "INFO",
        message: log,
      };
    });

    setLogs(parsedLogs);
  }, [liveLogs, isLive]);

  // Auto-scroll to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const copyToClipboard = () => {
    const text = logs.map((log) => `[${log.timestamp}] ${log.agent}: ${log.message}`).join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const displayedDiff = diff || defaultDiff;

  return (
    <div className="space-y-6">
      {/* Terminal Window */}
      <div className="rounded-lg border border-border overflow-hidden bg-black/50">
        <div className="flex items-center justify-between px-4 py-2 bg-border/50 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/50" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
              <div className="w-3 h-3 rounded-full bg-green-500/50" />
            </div>
            <span className="text-xs font-mono text-gray-500 ml-2">
              {isLive ? (
                <span className="flex items-center gap-2">
                  <Terminal className="w-3 h-3" />
                  Live Pipeline Output
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                </span>
              ) : (
                "Agent Intelligence Console"
              )}
            </span>
          </div>
          <button
            onClick={copyToClipboard}
            className="p-1.5 hover:bg-primary/10 rounded transition-colors group"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-500" />
            ) : (
              <Copy className="w-4 h-4 text-gray-500 group-hover:text-primary" />
            )}
          </button>
        </div>

        <div className="p-4 h-64 overflow-y-auto font-mono text-xs space-y-1">
          {logs.length === 0 && isLive && (
            <div className="text-gray-500 flex items-center gap-2">
              <span className="animate-pulse">Waiting for pipeline output...</span>
            </div>
          )}
          {logs.map((log, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-3"
            >
              <span className="text-gray-600">[{log.timestamp}]</span>
              <span
                className={
                  log.agent === "Sanitizer" ? "text-purple-400"
                  : log.agent === "Detective" ? "text-indigo-400"
                  : log.agent === "Reasoner" ? "text-purple-400"
                  : log.agent === "Verifier" ? "text-indigo-400"
                  : log.agent === "Publisher" ? "text-purple-400"
                  : "text-gray-400"
                }
              >
                {log.agent}:
              </span>
              <span className="text-gray-300">
                {log.message.includes("REDACTED") ? (
                  <>
                    {log.message.replace(/<REDACTED>/g, "")}
                    <span className="redacted-block font-semibold">&lt;REDACTED&gt;</span>
                  </>
                ) : (
                  log.message
                )}
              </span>
            </motion.div>
          ))}
          <div ref={logsEndRef} />
          <div className="flex gap-1 mt-2">
            <span className="text-primary">▊</span>
            <span className="text-gray-600 animate-pulse">_</span>
          </div>
        </div>
      </div>

      {/* Diff Viewer */}
      <div className="rounded-lg border border-border overflow-hidden bg-black/50">
        <div className="px-4 py-2 bg-border/50 border-b border-border">
          <span className="text-xs font-mono text-gray-500">
            {isLive && diff ? "Generated Patch (Unified Diff)" : "Proposed Fix (Unified Diff)"}
          </span>
        </div>
        <div className="p-4 font-mono text-xs overflow-x-auto max-h-64 overflow-y-auto">
          <pre className="text-gray-400">
            {displayedDiff.split("\n").map((line, idx) => (
              <div
                key={idx}
                className={
                  line.startsWith("+") && !line.startsWith("+++")
                    ? "bg-green-500/10 text-green-400"
                    : line.startsWith("-") && !line.startsWith("---")
                    ? "bg-red-500/10 text-red-400"
                    : line.startsWith("@@")
                    ? "text-cyan-400"
                    : ""
                }
              >
                {line}
              </div>
            ))}
          </pre>
        </div>
      </div>
    </div>
  );
}
