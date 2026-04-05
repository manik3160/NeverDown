"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Activity, 
  History, 
  Settings
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (path: string) => {
    return pathname === path ? "bg-blue-600/20 text-blue-400 border-r-2 border-blue-500" : "text-gray-400 hover:text-white hover:bg-white/5";
  };

  return (
    <div className="w-64 h-screen bg-[#0a0a0b] border-r border-[#1f2937] flex flex-col fixed left-0 top-0">
      {/* Logo Area */}
      <div className="p-6 border-b border-[#1f2937] flex items-center gap-3">
        <span className="font-bold text-xl tracking-tight text-white">Never Down</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 space-y-1">
        <div className="px-4 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Overview
        </div>
        
        <Link 
          href="/dashboard" 
          className={`flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors ${isActive("/dashboard")}`}
        >
          <LayoutDashboard className="w-5 h-5" />
          Dashboard
        </Link>

        <Link 
          href="/pipelines" 
          className={`flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors ${isActive("/pipelines")}`}
        >
          <Activity className="w-5 h-5" />
          Active Pipelines
        </Link>
        
        <Link 
          href="/incidents" 
          className={`flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors ${isActive("/incidents")}`}
        >
          <History className="w-5 h-5" />
          Incident History
        </Link>
      </nav>

      {/* Footer / Settings */}
      <div className="p-4 border-t border-[#1f2937]">
        <Link 
          href="/settings" 
          className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${isActive("/settings")}`}
        >
          <Settings className="w-5 h-5" />
          Configuration
        </Link>
        <div className="mt-4 px-4 py-2 bg-[#1f2937]/50 rounded-lg border border-[#374151]">
           <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-xs text-gray-300 font-medium">SYSTEM: NOMINAL</span>
           </div>
        </div>
      </div>
    </div>
  );
}
