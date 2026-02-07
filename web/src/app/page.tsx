"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Github, CheckCircle, Rocket, LogOut } from "lucide-react";
import PipelineVisualizer from "@/components/PipelineVisualizer";
import AgentTerminal from "@/components/AgentTerminal";
import SandboxDashboard from "@/components/SandboxDashboard";
import DeployModal from "@/components/DeployModal";

const API_BASE = "http://localhost:8000/api/v1";

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  
  // Deploy modal state
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);

  useEffect(() => {
    // Check for token in URL (callback from GitHub)
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const user = params.get("username");

    if (token) {
      localStorage.setItem("github_token", token);
      if (user) localStorage.setItem("github_username", user);
      
      setIsConnected(true);
      setUsername(user);
      
      // Clean URL
      window.history.replaceState({}, document.title, "/");
    } else {
      // Check localStorage
      const storedToken = localStorage.getItem("github_token");
      if (storedToken) {
        setIsConnected(true);
        setUsername(localStorage.getItem("github_username"));
      }
    }
  }, []);

  const handleConnect = () => {
    if (isConnected) return;
    window.location.href = `${API_BASE}/auth/github/login`;
  };

  const handleLogout = () => {
    localStorage.removeItem("github_token");
    localStorage.removeItem("github_username");
    setIsConnected(false);
    setUsername(null);
  };

  const handleDeploy = async (repoUrl: string, title: string, logs: string) => {
    try {
      // Create incident via API
      const response = await fetch(`${API_BASE}/incidents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: title,
          description: `Automated fix request for ${repoUrl}`,
          severity: "medium",
          source: "manual",
          logs: logs || "Monitoring via webhooks",
          metadata: {
            repository: {
              url: repoUrl,
              branch: "main",
            },
            triggered_by: username || "web-ui",
          },
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create incident");
      }

      const incident = await response.json();
      
      // Redirect to monitoring page
      window.location.href = `/monitor/${incident.id}`;
    } catch (error) {
      console.error("Failed to create incident:", error);
      throw error;
    }
  };



  return (
    <main className="min-h-screen relative overflow-hidden">
      {/* Sticky Blur Header */}
      <header className="sticky top-0 z-50 blur-header h-16 flex items-center px-6 justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center font-bold text-white">
            N
          </div>
          <span className="font-bold text-xl tracking-tight">NeverDown</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs font-mono text-green-500">SYSTEM ONLINE</span>
          </div>
          
          {isConnected ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-md bg-green-500/10 text-green-500 border border-green-500/20 cursor-default">
                <CheckCircle className="w-4 h-4" />
                <span>{username ? `Connected: ${username}` : "Repo Connected"}</span>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-md transition-all"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={handleConnect}
              className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-md transition-all bg-white text-black hover:bg-gray-200"
            >
              <Github className="w-4 h-4" />
              <span>Connect Repo</span>
            </button>
          )}
        </div>
      </header>

      <div className="container mx-auto px-6 py-12 space-y-24">
        {/* Section 1: Hero & Pipeline Visualization */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[60vh]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-8"
          >
            <h1 className="text-6xl md:text-7xl font-bold leading-tight tracking-tighter text-balance">
              Production-Grade <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
                Autonomous DevOps.
              </span>
            </h1>
            <p className="text-xl text-gray-400 max-w-lg leading-relaxed">
              Sentinel-Flow monitors, detects, and fixes production incidents in real-time. No human intervention required.
            </p>
            <div className="flex gap-4">
              <button
                onClick={() => setIsDeployModalOpen(true)}
                disabled={!isConnected}
                className={`
                  flex items-center gap-2 px-8 py-4 bg-primary text-white font-bold rounded-lg 
                  hover:ring-2 hover:ring-primary/50 transition-all
                  ${!isConnected ? "opacity-50 cursor-not-allowed" : ""}
                `}
              >
                <Rocket className="w-5 h-5" />
                Deploy Sentinel
              </button>
              <button className="px-8 py-4 border border-border bg-background/50 text-white font-semibold rounded-lg hover:bg-white/5 transition-all">
                View Architecture
              </button>
            </div>
            
            {!isConnected && (
              <p className="text-sm text-yellow-500/80">
                ⚠️ Connect your GitHub account to deploy Sentinel
              </p>
            )}
          </motion.div>

          {/* Right Side: Pipeline Visualizer */}
          <div className="h-[600px] border border-border rounded-2xl bg-black/50 backdrop-blur-sm relative overflow-hidden">
            <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none" />
            <PipelineVisualizer />
          </div>
        </section>

        {/* Section 2: Agent Terminal */}
        <section className="space-y-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tight">Agent Intelligence Console</h2>
            <p className="text-gray-400 max-w-2xl">
              Real-time execution logs from Detective and Reasoner agents. Watch as they analyze stack traces and generate fixes autonomously.
            </p>
          </div>
          
          <AgentTerminal />
        </section>

        {/* Section 3: Verification Center */}
        <section className="space-y-8 pb-24">
          <div className="flex flex-col items-center text-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tight">Verification Center</h2>
            <p className="text-gray-400 max-w-2xl">
              Isolated sandbox environments where patches are tested, validated, and packaged into pull requests.
            </p>
          </div>
          
          <SandboxDashboard />
        </section>
      </div>
      
      {/* Background ambient glow */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full bg-primary/20 blur-[128px]" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] rounded-full bg-secondary/20 blur-[128px]" />
      </div>

      {/* Deploy Modal */}
      <DeployModal
        isOpen={isDeployModalOpen}
        onClose={() => setIsDeployModalOpen(false)}
        onDeploy={handleDeploy}
      />
    </main>
  );
}
