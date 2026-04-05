"use client";

import { useState, useEffect } from "react";
import { 
  Search, 
  Filter, 
  ArrowUpDown, 
  ChevronLeft, 
  ChevronRight,
  Clock,
  CheckCircle,
  AlertCircle
} from "lucide-react";

import { getApiBase } from "@/lib/api";

const API_BASE = getApiBase();

interface Incident {
  id: string;
  title: string;
  status: string;
  created_at: string;
  metadata: any;
}

export default function IncidentHistory() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  useEffect(() => {
    fetch(`${API_BASE}/incidents`)
      .then(res => res.json())
      .then(data => setIncidents(data))
      .catch(err => console.error("Failed to fetch incidents", err));
  }, []);

  // Filter logic
  const filteredIncidents = incidents.filter(incident => {
    const matchesSearch = incident.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          incident.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "All" || incident.status.toLowerCase() === statusFilter.toLowerCase();
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-8 space-y-8 h-screen flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Incident Management History</h1>
          <p className="text-gray-400 mt-1">Audit log and historical records of all autonomous interventions.</p>
        </div>
        <div className="flex items-center gap-4">
           <div className="px-3 py-1 bg-green-900/20 border border-green-900/50 rounded-full flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-xs font-bold text-green-500">Connected: manik3160</span>
           </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-xl">
           <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
           <input 
              type="text" 
              placeholder="Search incidents..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
           />
        </div>
        
        <div className="relative">
           <select 
              className="appearance-none pl-10 pr-8 py-2 bg-[#111827] border border-[#374151] rounded-lg text-sm text-gray-300 focus:outline-none cursor-pointer hover:border-gray-500 transition-colors"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
           >
              <option value="All">Filter: All</option>
              <option value="resolved">Resolved</option>
              <option value="awaiting_review">Awaiting Review</option>
              <option value="failed">Failed</option>
           </select>
           <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
        </div>

        <div className="relative">
           <select className="appearance-none pl-10 pr-8 py-2 bg-[#111827] border border-[#374151] rounded-lg text-sm text-gray-300 focus:outline-none cursor-pointer hover:border-gray-500 transition-colors">
              <option>Sort: Newest</option>
              <option>Sort: Oldest</option>
           </select>
           <ArrowUpDown className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 border border-[#1f2937] rounded-xl overflow-hidden bg-[#111827]/50 flex flex-col">
        <div className="overflow-auto flex-1">
           <table className="w-full text-left">
              <thead className="bg-[#1f2937]/50 text-xs font-medium text-gray-400 uppercase tracking-wider sticky top-0">
                 <tr>
                    <th className="px-6 py-4">ID</th>
                    <th className="px-6 py-4">Title</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Created</th>
                    <th className="px-6 py-4 text-right">Fix Time</th>
                 </tr>
              </thead>
              <tbody className="divide-y divide-[#1f2937]">
                 {filteredIncidents.length === 0 ? (
                    <tr>
                       <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                          No incidents found matching your criteria.
                       </td>
                    </tr>
                 ) : (
                    filteredIncidents.map((incident) => (
                       <tr key={incident.id} className="hover:bg-[#1f2937]/30 transition-colors group">
                          <td className="px-6 py-4 font-mono text-sm text-blue-400 group-hover:text-blue-300">
                             {incident.id.substring(0, 8).toUpperCase()}
                          </td>
                          <td className="px-6 py-4 font-medium text-gray-200">
                             {incident.title}
                          </td>
                          <td className="px-6 py-4">
                             <StatusBadge status={incident.status} />
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-400">
                             {new Date(incident.created_at).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-right text-sm text-gray-400 font-mono">
                             {incident.status === 'resolved' ? '3m 20s' : '-'}
                          </td>
                       </tr>
                    ))
                 )}
              </tbody>
           </table>
        </div>

        {/* Footer / Pagination */}
        <div className="p-4 border-t border-[#1f2937] bg-[#111827] flex justify-between items-center">
           <span className="text-sm text-gray-500">
              Showing <span className="text-white font-medium">{filteredIncidents.length}</span> of <span className="text-white font-medium">{incidents.length}</span> total incidents
           </span>
           <div className="flex gap-2">
              <button className="px-3 py-1.5 text-sm bg-[#1f2937] border border-[#374151] rounded text-gray-300 hover:text-white disabled:opacity-50">
                 Previous
              </button>
              <button className="px-3 py-1.5 text-sm bg-[#1f2937] border border-[#374151] rounded text-gray-300 hover:text-white">
                 Next
              </button>
           </div>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
   const normalizedStatus = status.toLowerCase();
   
   if (normalizedStatus === "resolved" || normalizedStatus === "completed") {
      return (
         <span className="px-3 py-1 rounded-full text-xs font-bold bg-green-500/10 text-green-500 border border-green-500/20">
            RESOLVED
         </span>
      );
   }
   
   if (normalizedStatus === "awaiting_review") {
      return (
         <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/10 text-blue-500 border border-blue-500/20">
            AWAITING REVIEW
         </span>
      );
   }

   if (normalizedStatus === "failed") {
      return (
         <span className="px-3 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-500 border border-red-500/20">
            FAILED
         </span>
      );
   }

   return (
      <span className="px-3 py-1 rounded-full text-xs font-bold bg-gray-500/10 text-gray-400 border border-gray-500/20">
         {status.toUpperCase().replace("_", " ")}
      </span>
   );
}
