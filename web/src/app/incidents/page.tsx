"use client";

import { useState, useEffect } from "react";
import { 
  Search, 
  Filter, 
  ArrowUpDown, 
  CheckCircle,
} from "lucide-react";
import { useRouter } from "next/navigation";

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
  const router = useRouter();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  useEffect(() => {
    fetch(`${API_BASE}/incidents`)
      .then(res => res.json())
      .then(data => setIncidents(Array.isArray(data) ? data : []))
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
    <div className="bg-[#fafafa] min-h-screen p-10 font-sans text-gray-900 flex flex-col">
      <div className="max-w-[1200px] w-full mx-auto flex-1 flex flex-col">
         {/* Header */}
         <div className="flex justify-between items-center mb-10 border-b border-gray-200 pb-6 shadow-sm">
           <div>
             <h1 className="text-3xl font-serif font-bold text-black tracking-tight">Incident Management History</h1>
             <p className="text-sm text-gray-500 mt-2">Audit log and historical records of all autonomous interventions.</p>
           </div>
           <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-green-50 border border-green-200 px-4 py-2 rounded-full shadow-sm">
                 <div className="w-2 h-2 rounded-full bg-green-500"></div>
                 <span className="text-[11px] font-extrabold text-green-700 tracking-[0.1em] uppercase">Connected: manik3160</span>
              </div>
           </div>
         </div>

         {/* Toolbar */}
         <div className="flex gap-4 mb-8">
           <div className="relative flex-1 max-w-xl">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input 
                 type="text" 
                 placeholder="Search incidents by ID or Title..." 
                 value={searchTerm}
                 onChange={(e) => setSearchTerm(e.target.value)}
                 className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black shadow-sm transition-all"
              />
           </div>
           
           <div className="relative">
              <select 
                 className="appearance-none pl-11 pr-10 py-3 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-gray-600 focus:outline-none cursor-pointer hover:border-gray-300 shadow-sm transition-all"
                 value={statusFilter}
                 onChange={(e) => setStatusFilter(e.target.value)}
              >
                 <option value="All">Filter: All</option>
                 <option value="resolved">Resolved</option>
                 <option value="awaiting_review">Awaiting Review</option>
                 <option value="failed">Failed</option>
              </select>
              <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
           </div>

           <div className="relative">
              <select className="appearance-none pl-11 pr-10 py-3 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-gray-600 focus:outline-none cursor-pointer hover:border-gray-300 shadow-sm transition-all">
                 <option>Sort: Newest</option>
                 <option>Sort: Oldest</option>
              </select>
              <ArrowUpDown className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
           </div>
         </div>

         {/* Table */}
         <div className="flex-1 bg-white rounded-2xl shadow-[0_4px_20px_-10px_rgba(0,0,0,0.05)] border border-gray-100 flex flex-col overflow-hidden">
           <div className="overflow-auto flex-1 p-1">
              <table className="w-full text-left text-sm">
                 <thead className="bg-white">
                    <tr className="text-[10px] text-gray-400 font-bold uppercase tracking-widest border-b border-gray-100/60 sticky top-0 bg-white z-10 shadow-[0_1px_0_0_rgba(0,0,0,0.05)]">
                       <th className="px-6 py-5 font-bold">ID</th>
                       <th className="px-6 py-5 font-bold">Title</th>
                       <th className="px-6 py-5 font-bold">Status</th>
                       <th className="px-6 py-5 font-bold">Created</th>
                       <th className="px-6 py-5 font-bold text-right">Fix Time</th>
                    </tr>
                 </thead>
                 <tbody className="divide-y divide-gray-50">
                    {filteredIncidents.length === 0 ? (
                       <tr>
                          <td colSpan={5} className="px-6 py-16 text-center">
                             <div className="text-gray-500 font-medium text-[13px]">No incidents found matching your criteria.</div>
                          </td>
                       </tr>
                    ) : (
                       filteredIncidents.map((incident) => (
                          <tr 
                             key={incident.id} 
                             onClick={() => router.push(`/dashboard/incident/${incident.id.toUpperCase()}`)}
                             className="hover:bg-gray-50/70 transition-colors group cursor-pointer"
                          >
                             <td className="px-6 py-6 font-mono text-[13px] text-gray-500 group-hover:text-black transition-colors align-top">
                                {incident.id.substring(0, 8).toUpperCase()}
                             </td>
                             <td className="px-6 py-6 font-medium text-gray-800 pr-12 leading-relaxed align-top">
                                {incident.title}
                             </td>
                             <td className="px-6 py-6 align-top">
                                <StatusBadge status={incident.status} />
                             </td>
                             <td className="px-6 py-6 text-[13px] font-medium text-gray-400 align-top">
                                {new Date(incident.created_at).toLocaleString(undefined, { 
                                     month: 'short', day: 'numeric', year: 'numeric', 
                                     hour: 'numeric', minute: '2-digit'
                                })}
                             </td>
                             <td className="px-6 py-6 text-right text-[13px] font-medium text-gray-400 align-top">
                                {incident.status === 'resolved' ? '3m 20s' : '-'}
                             </td>
                          </tr>
                       ))
                    )}
                 </tbody>
              </table>
           </div>

           {/* Footer / Pagination */}
           <div className="px-6 py-4 border-t border-gray-100 bg-[#fafafa]/50 flex justify-between items-center rounded-b-2xl">
              <span className="text-[13px] font-medium text-gray-500">
                 Showing <span className="text-black font-extrabold">{filteredIncidents.length}</span> of <span className="text-black font-extrabold">{incidents.length}</span> total incidents
              </span>
              <div className="flex gap-2">
                 <button className="px-4 py-2 text-[13px] font-bold bg-white border border-gray-200 rounded-lg text-gray-600 hover:text-black hover:border-gray-300 shadow-sm transition-all disabled:opacity-50">
                    Previous
                 </button>
                 <button className="px-4 py-2 text-[13px] font-bold bg-white border border-gray-200 rounded-lg text-gray-600 hover:text-black hover:border-gray-300 shadow-sm transition-all disabled:opacity-50">
                    Next
                 </button>
              </div>
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
         <span className="px-2.5 py-1 text-[10px] font-extrabold tracking-[0.1em] uppercase rounded-full border text-gray-600 bg-[#f9fafb] border-gray-200">
            RESOLVED
         </span>
      );
   }
   
   if (normalizedStatus === "awaiting_review" || normalizedStatus === "refining") {
      return (
         <span className="px-2.5 py-1 text-[10px] font-extrabold tracking-[0.1em] uppercase rounded-full border text-[#d97706] bg-[#fffbf0] border-[#fde68a]">
            {normalizedStatus.replace("_", " ")}
         </span>
      );
   }

   if (normalizedStatus === "failed") {
      return (
         <span className="px-2.5 py-1 text-[10px] font-extrabold tracking-[0.1em] uppercase rounded-full border text-red-600 bg-red-50 border-red-200">
            FAILED
         </span>
      );
   }

   if (normalizedStatus === "monitoring" || normalizedStatus === "verifying") {
      return (
         <span className="px-2.5 py-1 text-[10px] font-extrabold tracking-[0.1em] uppercase rounded-full border text-[#2563eb] bg-[#eff6ff] border-[#bfdbfe]">
            {normalizedStatus.replace("_", " ")}
         </span>
      );
   }

   return (
      <span className="px-2.5 py-1 text-[10px] font-extrabold tracking-[0.1em] uppercase rounded-full border text-gray-500 bg-gray-50 border-gray-200">
         {status.toUpperCase().replace("_", " ")}
      </span>
   );
}
