"use client";

import { motion } from "framer-motion";
import { Container, Database, GitPullRequest, CheckCircle } from "lucide-react";

interface SandboxDashboardProps {
  prUrl?: string | null;
}

export default function SandboxDashboard({ prUrl }: SandboxDashboardProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Card A: Docker Sandbox Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-lg border border-border bg-background/50 p-6 hover:ring-2 hover:ring-primary/50 transition-all"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-mono text-gray-500">SANDBOX STATUS</h3>
          <Container className="w-5 h-5 text-secondary" />
        </div>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center relative">
            <div className="w-6 h-6 rounded-full bg-green-500 animate-pulse" />
            <div className="absolute inset-0 rounded-full border-2 border-green-500 animate-ping" />
          </div>
          <div>
            <div className="text-2xl font-bold text-green-500">Active</div>
            <div className="text-xs text-gray-500">Docker Environment</div>
          </div>
        </div>

        <div className="space-y-2 text-xs font-mono">
          <div className="flex justify-between">
            <span className="text-gray-500">Image:</span>
            <span className="text-gray-300">python:3.11-slim</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Memory:</span>
            <span className="text-gray-300">512MB</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Network:</span>
            <span className="text-gray-300">Isolated</span>
          </div>
        </div>
      </motion.div>

      {/* Card B: Faker Data Synthesis */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="rounded-lg border border-border bg-background/50 p-6 hover:ring-2 hover:ring-primary/50 transition-all"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-mono text-gray-500">DATA SYNTHESIS</h3>
          <Database className="w-5 h-5 text-primary" />
        </div>

        <div className="mb-4">
          <div className="text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            10,000
          </div>
          <div className="text-xs text-gray-500 mt-1">Synthetic Rows Generated</div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Users</span>
            <span className="font-mono text-gray-300">3,450</span>
          </div>
          <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
            <div className="h-full bg-primary w-[35%]" />
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Transactions</span>
            <span className="font-mono text-gray-300">6,550</span>
          </div>
          <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
            <div className="h-full bg-secondary w-[65%]" />
          </div>
        </div>
      </motion.div>

      {/* Card C: PR Preview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="rounded-lg border border-border bg-background/50 p-6 hover:ring-2 hover:ring-primary/50 transition-all"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-mono text-gray-500">PULL REQUEST</h3>
          <GitPullRequest className="w-5 h-5 text-green-500" />
        </div>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-lg font-bold">
            N
          </div>
          <div>
            <div className="text-sm font-semibold">NeverDown Bot</div>
            <div className="text-xs text-gray-500 font-mono">neverdown/fix-06a09e5e</div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-gray-400">All checks passed</span>
          </div>

          {prUrl ? (
            <a
              href={prUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full py-2.5 px-4 rounded-lg bg-green-600 hover:bg-green-500 font-semibold text-white transition-all hover:ring-2 hover:ring-green-500/50 flex items-center justify-center gap-2"
            >
              <GitPullRequest className="w-4 h-4" />
              View Pull Request
            </a>
          ) : (
            <button className="w-full py-2.5 px-4 rounded-lg bg-primary hover:bg-primary/90 font-semibold text-white transition-all hover:ring-2 hover:ring-primary/50 flex items-center justify-center gap-2">
              <GitPullRequest className="w-4 h-4" />
              Open Pull Request
            </button>
          )}

          <div className="grid grid-cols-3 gap-2 text-xs text-center">
            <div>
              <div className="font-mono text-green-500">+12</div>
              <div className="text-gray-600">Added</div>
            </div>
            <div>
              <div className="font-mono text-red-500">-4</div>
              <div className="text-gray-600">Removed</div>
            </div>
            <div>
              <div className="font-mono text-gray-400">1</div>
              <div className="text-gray-600">Files</div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
