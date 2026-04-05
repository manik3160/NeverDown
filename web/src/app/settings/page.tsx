"use client";

import { Save, Github, Key, Webhook, ShieldAlert } from "lucide-react";

export default function Settings() {
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
              <button className="flex items-center gap-2 bg-[#1a1a1a] text-white px-6 py-2.5 rounded-lg text-sm font-bold tracking-wide hover:bg-black transition-colors shadow-md">
                 <Save className="w-4 h-4" />
                 Save Changes
              </button>
           </div>
         </div>

         {/* Content Grid */}
         <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Left Column (Nav/Anchors) */}
            <div className="md:col-span-1 space-y-2">
               <button className="w-full text-left px-4 py-3 rounded-xl bg-white border border-gray-200 text-sm font-bold text-black shadow-sm flex flex-col">
                  Integrations
                  <span className="text-[11px] font-medium text-gray-400 font-sans tracking-wide mt-0.5">GitHub, Webhooks, Auth</span>
               </button>
               <button className="w-full text-left px-4 py-3 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-black transition-colors flex flex-col">
                  AI Reasoner Settings
                  <span className="text-[11px] font-medium text-gray-400 font-sans tracking-wide mt-0.5">Model limits, Prompts</span>
               </button>
               <button className="w-full text-left px-4 py-3 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-black transition-colors flex flex-col">
                  Deployment Policies
                  <span className="text-[11px] font-medium text-gray-400 font-sans tracking-wide mt-0.5">Auto-approve thresholds</span>
               </button>
            </div>

            {/* Right Column (Form sections) */}
            <div className="md:col-span-2 space-y-8">
               
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
                          defaultValue="ghp_xxxxxxxxxxxxxxxxxxxxxx"
                          className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all"
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
                          defaultValue="sk-proj-xxxxxxxxxxxxxx"
                          className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all"
                        />
                     </div>
                  </div>
               </div>

               {/* Danger Zone */}
               <div className="bg-red-50/30 rounded-2xl border border-red-100 overflow-hidden">
                  <div className="px-6 py-5 border-b border-red-100 bg-red-50/50 flex items-center gap-3">
                     <ShieldAlert className="w-5 h-5 text-red-600" />
                     <h2 className="text-base font-bold text-red-900">Danger Zone</h2>
                  </div>
                  <div className="p-6 flex items-center justify-between">
                     <div>
                        <div className="text-sm font-bold text-gray-900">Halt All Autonomous Activity</div>
                        <div className="text-[12px] font-medium text-gray-500 mt-1">Instantly pauses the Sanatizer, Detective, and Reasoner agents.</div>
                     </div>
                     <button className="px-5 py-2.5 bg-red-50 text-red-600 border border-red-200 rounded-lg text-[13px] font-bold tracking-wide hover:bg-red-100 transition-colors shadow-sm focus:ring-2 focus:ring-offset-2 focus:ring-red-200">
                        Halt Agents
                     </button>
                  </div>
               </div>

            </div>
         </div>
      </div>
    </div>
  );
}
