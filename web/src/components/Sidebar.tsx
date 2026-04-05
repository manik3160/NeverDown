"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (path: string) => {
    return pathname === path 
      ? "text-white border-l-[3px] border-[#ff6b00] pl-[29px]"
      : "text-gray-400 hover:text-white pl-[32px] hover:bg-white/5";
  };

  return (
    <div className="w-64 h-screen bg-[#141414] border-r border-[#1f2937] flex flex-col fixed left-0 top-0">
      {/* Logo Area */}
      <div className="p-8 pb-12 mt-4">
        <span className="font-serif font-bold text-2xl tracking-tight text-white">NeverDown</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-6">
        <Link 
          href="/dashboard" 
          className={`flex items-center py-2 text-[15px] font-medium transition-colors w-full ${isActive("/dashboard")}`}
        >
          Dashboard
        </Link>

        <Link 
          href="/incidents" 
          className={`flex items-center py-2 text-[15px] font-medium transition-colors w-full ${isActive("/incidents")}`}
        >
          Incident Logs
        </Link>
        


        <Link 
          href="/settings" 
          className={`flex items-center py-2 text-[15px] font-medium transition-colors w-full ${isActive("/settings")}`}
        >
          Settings
        </Link>
      </nav>

      {/* Footer Version Info */}
      <div className="p-6">
        <div className="bg-[#1f1f1f] rounded-lg p-4 border border-[#2a2a2a]">
           <div className="text-[10px] text-gray-500 font-medium uppercase tracking-wider mb-2">Current Version</div>
           <div className="text-xs text-gray-300 font-mono">v2.4.12-stable</div>
        </div>
      </div>
    </div>
  );
}
