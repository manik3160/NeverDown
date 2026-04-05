"use client";

import { useState, useEffect } from "react";
import { Github, CheckCircle, AlertTriangle, Shield, Zap, Activity } from "lucide-react";
import DeployModal from "@/components/DeployModal";

import { getApiBase } from "@/lib/api";

const API_BASE = getApiBase();

export default function Dashboard() {
  const [isConnected, setIsConnected] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
  const [incidents, setIncidents] = useState<any[]>([]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const user = params.get("username");

    if (token) {
      localStorage.setItem("github_token", token);
      if (user) localStorage.setItem("github_username", user);
      setIsConnected(true);
      setUsername(user);
      window.history.replaceState({}, document.title, "/dashboard");
    } else {
      const storedToken = localStorage.getItem("github_token");
      if (storedToken) {
        setIsConnected(true);
        setUsername(localStorage.getItem("github_username"));
      }
    }

    fetch(`${API_BASE}/incidents`)
      .then(res => res.json())
      .then(data => setIncidents(data.slice(0, 5)))
      .catch(err => console.error("Failed to fetch incidents", err));
  }, []);

  const handleConnect = () => {
    if (isConnected) return;
    window.location.href = `${API_BASE}/auth/github/login`;
  };

  const handleDeploy = async (repoUrl: string, title: string, logs: string) => {
    try {
      const response = await fetch(`${API_BASE}/incidents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title,
          description: `Automated fix request for ${repoUrl}`,
          severity: "medium",
          source: "manual",
          logs: logs || "Monitoring via webhooks",
          metadata: {
            repository: { url: repoUrl, branch: "main" },
            triggered_by: username || "web-ui",
          },
        }),
      });

      if (!response.ok) throw new Error("Failed to create incident");
      const incident = await response.json();
      window.location.href = `/pipelines`;
    } catch (error) {
      console.error("Failed to create incident:", error);
    }
  };

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard Overview</h1>
          <p className="text-gray-400 mt-1">Real-time autonomous incident remediation metrics.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#111827] border border-[#1f2937]">
             <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
             <span className="text-sm font-medium text-gray-300">us-east-1</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-sm">
            {username ? username.substring(0, 2).toUpperCase() : "JD"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6 relative overflow-hidden">
          <div className="flex justify-between items-start mb-4">
             <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm font-semibold text-green-500 tracking-wider">ACTIVE NOW</span>
             </div>
             <AlertTriangle className="w-8 h-8 text-yellow-500" />
          </div>
          <div className="space-y-1">
             <span className="text-5xl font-bold text-white">2</span>
             <span className="text-gray-400 text-lg ml-2">incidents</span>
          </div>
          <div className="mt-4 text-xs text-yellow-500/80 font-medium">
             Requires human oversight
          </div>
        </div>

        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6">
           <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">TODAY&apos;S STATS</div>
           <div className="flex items-end gap-8">
              <div>
                 <div className="text-4xl font-bold text-white">14</div>
                 <div className="text-sm text-gray-500 mt-1">Detected</div>
              </div>
              <div className="h-10 w-[1px] bg-[#1f2937]"></div>
              <div>
                 <div className="text-4xl font-bold text-green-500">12</div>
                 <div className="text-sm text-gray-500 mt-1">Fixed</div>
              </div>
           </div>
           <div className="mt-4 flex items-center gap-1 text-xs text-green-500 font-medium">
              <Activity className="w-3 h-3" />
              +12% vs yesterday
           </div>
        </div>

        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6">
           <div className="flex justify-between items-start mb-6">
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">AUTO-FIX RATE</div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-500/20 text-green-500 border border-green-500/20">High Efficiency</span>
           </div>
           <div className="flex items-end gap-1 mb-2">
              <span className="text-5xl font-bold text-white">87</span>
              <span className="text-xl text-gray-400 mb-1">%</span>
           </div>
           <div className="w-full h-1.5 bg-[#1f2937] rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 to-green-400 w-[87%] rounded-full"></div>
           </div>
        </div>
      </div>

      <div className="bg-[#111827] border border-[#1f2937] rounded-xl overflow-hidden">
        <div className="p-4 border-b border-[#1f2937] flex justify-between items-center bg-[#1f2937]/30">
           <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-gray-400" />
              <h3 className="font-semibold text-sm tracking-wide">RECENT ACTIVITY</h3>
           </div>
           <button className="text-xs text-blue-400 hover:text-blue-300 font-medium">View All Logs</button>
        </div>
        <div className="divide-y divide-[#1f2937]">
           <div className="p-4 flex items-center gap-4 hover:bg-[#1f2937]/30 transition-colors">
              <div className="p-2 rounded bg-yellow-500/10 border border-yellow-500/20">
                 <AlertTriangle className="w-5 h-5 text-yellow-500" />
              </div>
              <div className="flex-1 min-w-0">
                 <div className="flex items-center gap-3">
                    <span className="font-medium text-white truncate">CI Failure detected in pipeline #402</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#1f2937] text-gray-400 border border-[#374151]">ID: inc-4921</span>
                 </div>
                 <div className="text-sm text-gray-500 mt-0.5">10:42 AM • Analyzing build logs for root cause</div>
              </div>
              <button className="px-3 py-1.5 text-xs font-medium bg-blue-600/10 text-blue-400 border border-blue-600/20 rounded hover:bg-blue-600/20">
                 • Verifying
              </button>
           </div>
           <div className="p-4 flex items-center gap-4 hover:bg-[#1f2937]/30 transition-colors">
              <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20">
                 <Zap className="w-5 h-5 text-blue-500" />
              </div>
              <div className="flex-1 min-w-0">
                 <div className="flex items-center gap-3">
                    <span className="font-medium text-white truncate">DB Query Timeout - High Latency</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#1f2937] text-gray-400 border border-[#374151]">ID: inc-4920</span>
                 </div>
                 <div className="text-sm text-gray-500 mt-0.5">10:15 AM • Optimizing index usage on users_table</div>
              </div>
              <button className="px-3 py-1.5 text-xs font-medium bg-blue-600/10 text-blue-400 border border-blue-600/20 rounded hover:bg-blue-600/20">
                 • Refining
              </button>
           </div>
           <div className="p-4 flex items-center gap-4 hover:bg-[#1f2937]/30 transition-colors">
              <div className="p-2 rounded bg-green-500/10 border border-green-500/20">
                 <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <div className="flex-1 min-w-0">
                 <div className="flex items-center gap-3">
                    <span className="font-medium text-white truncate">Redis Connection Lost</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#1f2937] text-gray-400 border border-[#374151]">ID: inc-4919</span>
                 </div>
                 <div className="text-sm text-gray-500 mt-0.5">09:55 AM • Instance rebooted and reconnected successfully</div>
              </div>
              <button className="px-3 py-1.5 text-xs font-medium bg-green-500/10 text-green-500 border border-green-500/20 rounded hover:bg-green-500/20">
                 Resolved
              </button>
           </div>
        </div>
      </div>

      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6">
         <h3 className="font-bold text-sm tracking-wide mb-6">SYSTEM HEALTH STATUS</h3>
         <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <HealthIndicator label="Webhook" status="ONLINE" />
            <HealthIndicator label="Docker" status="ONLINE" />
            <HealthIndicator label="LLM API" status="ONLINE" />
            <HealthIndicator label="GitHub" status="ONLINE" />
         </div>
      </div>

      <div className="mt-8 flex justify-end">
          {!isConnected ? (
            <button
              onClick={handleConnect}
              className="flex items-center gap-2 px-6 py-3 bg-white text-black font-semibold rounded-lg hover:bg-gray-200 transition-all"
            >
              <Github className="w-5 h-5" />
              Connect GitHub Repo
            </button>
          ) : (
             <button
                onClick={() => setIsDeployModalOpen(true)}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-500 transition-all shadow-lg shadow-blue-900/20"
             >
                <Zap className="w-5 h-5" />
                Trigger Manual Incident
             </button>
          )}
      </div>

      <DeployModal
        isOpen={isDeployModalOpen}
        onClose={() => setIsDeployModalOpen(false)}
        onDeploy={handleDeploy}
      />
    </div>
  );
}

function HealthIndicator({ label, status }: { label: string, status: string }) {
   return (
      <div className="flex items-center justify-between p-3 rounded bg-[#1f2937]/30 border border-[#374151]">
         <div className="flex items-center gap-3">
            <Shield className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-300">{label}</span>
         </div>
         <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-[10px] font-bold text-green-500 tracking-wide">{status}</span>
         </div>
      </div>
   );
}
