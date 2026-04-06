"use client";

import { useState, useEffect } from "react";
import { Save, Github, Key, ShieldAlert, CheckCircle2, BrainCircuit, Activity, Sliders, Target } from "lucide-react";

export default function Settings() {
  const [activeTab, setActiveTab] = useState("integrations");
  const [githubToken, setGithubToken] = useState("");
  const [llmKey, setLlmKey] = useState("");
  const [isHalted, setIsHalted] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showSavedToast, setShowSavedToast] = useState(false);

  useEffect(() => {
    setGithubToken(localStorage.getItem("github_token") || "");
    setLlmKey(localStorage.getItem("llm_api_key") || "");
    setIsHalted(localStorage.getItem("agents_halted") === "true");
  }, []);

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      localStorage.setItem("github_token", githubToken);
      localStorage.setItem("llm_api_key", llmKey);
      setIsSaving(false);
      setShowSavedToast(true);
      setTimeout(() => setShowSavedToast(false), 2000);
    }, 400); // Simulate network delay
  };

  const toggleHalt = () => {
    const newState = !isHalted;
    setIsHalted(newState);
    localStorage.setItem("agents_halted", String(newState));
  };

  return (
    <div className="bg-[#fafafa] min-h-screen p-10 font-sans text-gray-900 flex flex-col">
      <div className="max-w-[1000px] mx-auto w-full flex-1 flex flex-col">
         {/* Header */}
         <div className="flex justify-between items-center mb-10 border-b border-gray-200 pb-6 shadow-sm">
           <div>
             <h1 className="text-3xl font-serif font-bold text-black tracking-tight">System Configuration</h1>
             <p className="text-sm text-gray-500 mt-2">Manage your autonomous agents, integrations, and operational policies</p>
           </div>
           <div className="flex items-center gap-4">
              {showSavedToast && (
                <span className="text-sm font-bold text-green-600 flex items-center gap-1.5 animate-in fade-in slide-in-from-right-4">
                  <CheckCircle2 className="w-4 h-4" />
                  Saved!
                </span>
              )}
              <button 
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2 bg-[#1a1a1a] text-white px-6 py-2.5 rounded-lg text-sm font-bold tracking-wide hover:bg-black transition-colors shadow-md disabled:bg-gray-400"
              >
                 <Save className="w-4 h-4" />
                 {isSaving ? "Saving..." : "Save Changes"}
              </button>
           </div>
         </div>

         {/* Content Grid */}
         <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Left Column (Nav/Anchors) */}
            <div className="md:col-span-1 space-y-2">
               <button 
                 onClick={() => setActiveTab("integrations")}
                 className={`w-full text-left px-4 py-3 rounded-xl flex flex-col transition-all ${
                   activeTab === "integrations" 
                     ? "bg-white border border-gray-200 shadow-sm text-black"
                     : "text-gray-600 hover:bg-gray-100 hover:text-black border border-transparent"
                 }`}
               >
                  <span className="text-sm font-bold">Integrations</span>
                  <span className="text-[11px] font-medium text-gray-400 font-sans tracking-wide mt-0.5">GitHub, Webhooks, Auth</span>
               </button>
               <button 
                 onClick={() => setActiveTab("reasoner")}
                 className={`w-full text-left px-4 py-3 rounded-xl flex flex-col transition-all ${
                   activeTab === "reasoner" 
                     ? "bg-white border border-gray-200 shadow-sm text-black"
                     : "text-gray-600 hover:bg-gray-100 hover:text-black border border-transparent"
                 }`}
               >
                  <span className="text-sm font-bold">AI Reasoner Settings</span>
                  <span className="text-[11px] font-medium text-gray-400 font-sans tracking-wide mt-0.5">Model limits, Prompts</span>
               </button>
               <button 
                 onClick={() => setActiveTab("policies")}
                 className={`w-full text-left px-4 py-3 rounded-xl flex flex-col transition-all ${
                   activeTab === "policies" 
                     ? "bg-white border border-gray-200 shadow-sm text-black"
                     : "text-gray-600 hover:bg-gray-100 hover:text-black border border-transparent"
                 }`}
               >
                  <span className="text-sm font-bold">Deployment Policies</span>
                  <span className="text-[11px] font-medium text-gray-400 font-sans tracking-wide mt-0.5">Auto-approve thresholds</span>
               </button>
            </div>

            {/* Right Column (Form sections) */}
            <div className="md:col-span-2 space-y-8 animate-in fade-in duration-300">
               
               {activeTab === "integrations" && (
                 <>
                   {/* Integrations Module */}
                   <div className="bg-white rounded-2xl shadow-[0_4px_20px_-10px_rgba(0,0,0,0.05)] border border-gray-100 overflow-hidden">
                      <div className="px-6 py-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
                         <Github className="w-5 h-5 text-gray-700" />
                         <h2 className="text-base font-bold text-gray-900">Version Control Integrations</h2>
                      </div>
                      <div className="p-6 space-y-6">
                         <div className="space-y-2">
                            <label className="text-[13px] font-bold text-gray-700 tracking-wide">
                              GitHub Access Token
                            </label>
                            <input
                              type="password"
                              value={githubToken}
                              onChange={(e) => setGithubToken(e.target.value)}
                              placeholder="ghp_..."
                              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all"
                            />
                            <p className="text-[11px] font-semibold text-gray-400">Required: repo, workflow, write:packages</p>
                         </div>
                      </div>
                   </div>

                   {/* API Key Module */}
                   <div className="bg-white rounded-2xl shadow-[0_4px_20px_-10px_rgba(0,0,0,0.05)] border border-gray-100 overflow-hidden">
                      <div className="px-6 py-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
                         <Key className="w-5 h-5 text-gray-700" />
                         <h2 className="text-base font-bold text-gray-900">NeverDown AI Engine</h2>
                      </div>
                      <div className="p-6 space-y-6">
                         <div className="space-y-2">
                            <label className="text-[13px] font-bold text-gray-700 tracking-wide">
                              LLM Provider API Key
                            </label>
                            <input
                              type="password"
                              value={llmKey}
                              onChange={(e) => setLlmKey(e.target.value)}
                              placeholder="sk-proj-..."
                              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all"
                            />
                         </div>
                      </div>
                   </div>

                   {/* Danger Zone */}
                   <div className={`rounded-2xl border overflow-hidden transition-colors ${isHalted ? "bg-red-50 border-red-200" : "bg-red-50/30 border-red-100"}`}>
                      <div className={`px-6 py-5 border-b flex items-center gap-3 transition-colors ${isHalted ? "border-red-200 bg-red-100/50" : "border-red-100 bg-red-50/50"}`}>
                         <ShieldAlert className="w-5 h-5 text-red-600" />
                         <h2 className="text-base font-bold text-red-900">Danger Zone</h2>
                      </div>
                      <div className="p-6 flex items-center justify-between">
                         <div>
                            <div className="text-sm font-bold text-gray-900">
                               {isHalted ? "Agents Currently Halted" : "Halt All Autonomous Activity"}
                            </div>
                            <div className="text-[12px] font-medium text-gray-500 mt-1">
                               {isHalted 
                                 ? "Agents will not detect or resolve incidents until resumed." 
                                 : "Instantly pauses the Sanatizer, Detective, and Reasoner agents."}
                            </div>
                         </div>
                         <button 
                           onClick={toggleHalt}
                           className={`px-5 py-2.5 rounded-lg text-[13px] font-bold tracking-wide shadow-sm focus:ring-2 focus:ring-offset-2 transition-colors ${
                             isHalted 
                               ? "bg-green-500 text-white border-transparent hover:bg-green-600 focus:ring-green-500"
                               : "bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 focus:ring-red-200"
                           }`}
                         >
                            {isHalted ? "Resume Agents" : "Halt Agents"}
                         </button>
                      </div>
                   </div>
                 </>
               )}

               {activeTab === "reasoner" && (
                 <>
                   <div className="bg-white rounded-2xl shadow-[0_4px_20px_-10px_rgba(0,0,0,0.05)] border border-gray-100 overflow-hidden">
                      <div className="px-6 py-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
                         <BrainCircuit className="w-5 h-5 text-gray-700" />
                         <h2 className="text-base font-bold text-gray-900">AI Model Configuration</h2>
                      </div>
                      <div className="p-6 space-y-6">
                         <div className="space-y-2">
                            <label className="text-[13px] font-bold text-gray-700 tracking-wide">
                              Active Model
                            </label>
                            <select className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all appearance-none">
                              <option>gpt-4o-2024-05-13 (Recommended)</option>
                              <option>gpt-4-turbo-preview</option>
                              <option>claude-3-5-sonnet-20240620</option>
                            </select>
                         </div>
                         <div className="space-y-2">
                            <label className="text-[13px] font-bold text-gray-700 tracking-wide">
                              Context Window Limit (Tokens)
                            </label>
                            <input
                              type="number"
                              defaultValue={128000}
                              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:outline-none focus:border-black transition-all"
                            />
                         </div>
                         <div className="space-y-2">
                            <label className="text-[13px] font-bold text-gray-700 tracking-wide">
                              Global Temperature
                            </label>
                            <div className="flex items-center gap-4">
                              <input type="range" min="0" max="100" defaultValue="20" className="flex-1 accent-black" />
                              <span className="text-sm font-bold text-gray-600 bg-gray-100 px-3 py-1 rounded-md">0.2</span>
                            </div>
                            <p className="text-[11px] font-semibold text-gray-400 pt-1">Lower values ensure deterministic log parsing.</p>
                         </div>
                      </div>
                   </div>

                   <div className="bg-white rounded-2xl shadow-[0_4px_20px_-10px_rgba(0,0,0,0.05)] border border-gray-100 overflow-hidden">
                      <div className="px-6 py-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
                         <Sliders className="w-5 h-5 text-gray-700" />
                         <h2 className="text-base font-bold text-gray-900">Custom Instructions</h2>
                      </div>
                      <div className="p-6 space-y-6">
                         <div className="space-y-2">
                            <label className="text-[13px] font-bold text-gray-700 tracking-wide">
                              Base System Prompt Overlay
                            </label>
                            <textarea
                              rows={4}
                              defaultValue={"You are an autonomous SRE agent for NeverDown.\nPrioritize zero-downtime hotfixes over refactoring. Always use Type-Safe approaches."}
                              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-700 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all resize-none font-mono"
                            />
                         </div>
                      </div>
                   </div>
                 </>
               )}

               {activeTab === "policies" && (
                 <>
                   <div className="bg-white rounded-2xl shadow-[0_4px_20px_-10px_rgba(0,0,0,0.05)] border border-gray-100 overflow-hidden">
                      <div className="px-6 py-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
                         <Target className="w-5 h-5 text-gray-700" />
                         <h2 className="text-base font-bold text-gray-900">Pipeline Overrides</h2>
                      </div>
                      <div className="p-6 space-y-6">
                         <label className="flex items-start gap-3 cursor-pointer group">
                           <div className="relative flex items-start pt-0.5">
                             <input type="checkbox" defaultChecked className="peer w-5 h-5 appearance-none rounded border-2 border-gray-300 checked:bg-black checked:border-black transition-colors" />
                             <CheckCircle2 className="w-4 h-4 text-white absolute left-0.5 top-1 pointer-events-none opacity-0 peer-checked:opacity-100" />
                           </div>
                           <div>
                             <div className="text-[14px] font-bold text-gray-900 group-hover:text-black">Auto-Approve Low Risk Patches</div>
                             <div className="text-[12px] font-medium text-gray-500 mt-0.5">Permits Verifier agent to directly merge PRs under 10 lines of diff that pass tests.</div>
                           </div>
                         </label>

                         <label className="flex items-start gap-3 cursor-pointer group">
                           <div className="relative flex items-start pt-0.5">
                             <input type="checkbox" defaultChecked className="peer w-5 h-5 appearance-none rounded border-2 border-gray-300 checked:bg-black checked:border-black transition-colors" />
                             <CheckCircle2 className="w-4 h-4 text-white absolute left-0.5 top-1 pointer-events-none opacity-0 peer-checked:opacity-100" />
                           </div>
                           <div>
                             <div className="text-[14px] font-bold text-gray-900 group-hover:text-black">Require Manual Code Review on Database Alterations</div>
                             <div className="text-[12px] font-medium text-gray-500 mt-0.5">If the patch modifies an ORM model or SQL migration, enforce human review.</div>
                           </div>
                         </label>

                         <label className="flex items-start gap-3 cursor-pointer group">
                           <div className="relative flex items-start pt-0.5">
                             <input type="checkbox" defaultChecked className="peer w-5 h-5 appearance-none rounded border-2 border-gray-300 checked:bg-orange-500 checked:border-orange-500 transition-colors" />
                             <CheckCircle2 className="w-4 h-4 text-white absolute left-0.5 top-1 pointer-events-none opacity-0 peer-checked:opacity-100" />
                           </div>
                           <div>
                             <div className="text-[14px] font-bold text-gray-900 group-hover:text-orange-600 transition-colors">Alert via Slack on Critical Failures</div>
                             <div className="text-[12px] font-medium text-gray-500 mt-0.5">Ping the configured Slack Webhook when remediation yields no viable fixes.</div>
                           </div>
                         </label>
                      </div>
                   </div>
                 </>
               )}

            </div>
         </div>
      </div>
    </div>
  );
}
