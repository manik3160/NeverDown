"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Zap, AlertTriangle, Loader2 } from "lucide-react";

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
      await onDeploy(
        repoUrl.trim(),
        `Monitor ${new URL(repoUrl).pathname.split("/").pop()}`,
        ""
      );
      setRepoUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to trigger incident");
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
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[600px] z-[60]"
          >
            <div className="bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden text-black font-sans">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 bg-gray-50/50">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-[#fff5eb] border border-[#ffe0cc] rounded-xl flex items-center justify-center shadow-sm">
                    <Zap className="w-5 h-5 text-[#ff6b00]" fill="currentColor" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold tracking-tight text-gray-900">Trigger Manual Incident</h2>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mt-1">Start autonomous monitoring</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-100 text-gray-400 hover:text-black rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="p-6 pb-8 space-y-6">
                {/* Repository URL */}
                <div className="space-y-2">
                  <label className="text-[13px] font-bold text-gray-700 tracking-wide">
                    Repository URL <span className="text-orange-500">*</span>
                  </label>
                  <input
                    type="url"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="https://github.com/owner/repo"
                    className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm font-medium text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black shadow-sm transition-all"
                    disabled={isLoading}
                    autoFocus
                  />
                  <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide pt-1">
                    NeverDown will monitor this repository for CI/CD failures
                  </p>
                </div>

                {/* Info Box */}
                <div className="px-5 py-4 bg-blue-50/50 border border-blue-100 rounded-xl shadow-sm">
                  <h4 className="text-[11px] font-bold text-blue-800 uppercase tracking-widest mb-3">How it works:</h4>
                  <ul className="text-[13px] font-medium text-gray-600 space-y-2">
                    <li className="flex gap-2"><span className="text-blue-500">•</span> <strong>Sanitizer</strong> scans for exposed secrets</li>
                    <li className="flex gap-2"><span className="text-blue-500">•</span> <strong>Detective</strong> analyzes CI/CD failure logs automatically</li>
                    <li className="flex gap-2"><span className="text-blue-500">•</span> <strong>Reasoner</strong> generates fixes using AI</li>
                    <li className="flex gap-2"><span className="text-blue-500">•</span> <strong>Verifier</strong> tests patches in isolated sandbox</li>
                    <li className="flex gap-2"><span className="text-blue-500">•</span> <strong>Publisher</strong> creates a pull request with the verified patch</li>
                  </ul>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="flex items-center gap-3 px-4 py-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-semibold shadow-sm">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-4 pt-4">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 px-6 py-3.5 bg-white border border-gray-200 rounded-xl text-sm font-bold tracking-wide text-gray-700 hover:bg-gray-50 hover:text-black transition-colors shadow-sm disabled:opacity-50"
                    disabled={isLoading}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 px-6 py-3.5 bg-[#1a1a1a] text-white rounded-xl text-sm font-bold tracking-wide hover:bg-black transition-colors shadow-md flex items-center justify-center gap-2 disabled:opacity-50 disabled:bg-gray-400"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        Triggering...
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 text-[#ff6b00]" strokeWidth={2.5} />
                        Trigger Incident
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
