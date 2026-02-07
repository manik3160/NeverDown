"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Rocket, AlertTriangle, Loader2 } from "lucide-react";

interface DeployModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDeploy: (repoUrl: string, title: string, logs: string) => Promise<void>;
}

export default function DeployModal({ isOpen, onClose, onDeploy }: DeployModalProps) {
  const [repoUrl, setRepoUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!repoUrl.trim()) {
      setError("Repository URL is required");
      return;
    }

    // Validate GitHub URL format
    try {
      const url = new URL(repoUrl.trim());
      if (!url.hostname.includes('github.com')) {
        setError("Please enter a valid GitHub repository URL");
        return;
      }
    } catch {
      setError("Please enter a valid URL");
      return;
    }

    setIsLoading(true);
    try {
      // The system will monitor this repo via webhooks
      // For demo purposes, we'll trigger with empty logs (webhook will provide real logs)
      await onDeploy(
        repoUrl.trim(),
        `Monitor ${new URL(repoUrl).pathname.split("/").pop()}`,
        "" // Empty logs - webhook will provide actual CI/CD failure logs
      );
      setRepoUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start monitoring");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl z-50"
          >
            <div className="bg-zinc-900 border border-border rounded-2xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/20 rounded-xl flex items-center justify-center">
                    <Rocket className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold">Deploy Sentinel</h2>
                    <p className="text-sm text-gray-400">Start autonomous monitoring</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="p-6 space-y-5">
                {/* Repository URL */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-300">
                    Repository URL <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="url"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="https://github.com/owner/repo"
                    className="w-full px-4 py-3 bg-black border border-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                    disabled={isLoading}
                    autoFocus
                  />
                  <p className="text-xs text-gray-500">
                    Sentinel will monitor this repository for CI/CD failures via GitHub webhooks
                  </p>
                </div>

                {/* Info Box */}
                <div className="px-4 py-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <h4 className="text-sm font-semibold text-blue-400 mb-2">How it works:</h4>
                  <ul className="text-xs text-gray-400 space-y-1">
                    <li>• <strong>Sanitizer</strong> scans for exposed secrets</li>
                    <li>• <strong>Detective</strong> analyzes CI/CD failure logs automatically</li>
                    <li>• <strong>Reasoner</strong> generates fixes using AI</li>
                    <li>• <strong>Verifier</strong> tests patches in isolated sandbox</li>
                    <li>• <strong>Publisher</strong> creates pull request with fix</li>
                  </ul>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 px-6 py-3 bg-white/5 border border-border rounded-lg font-semibold hover:bg-white/10 transition-colors"
                    disabled={isLoading}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 px-6 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Deploying...
                      </>
                    ) : (
                      <>
                        <Rocket className="w-4 h-4" />
                        Deploy Sentinel
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
