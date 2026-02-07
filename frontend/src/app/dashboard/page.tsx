'use client';

import { useIncidents } from '@/hooks/useIncidents';
import { IncidentCard } from '@/components/incidents/IncidentCard';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { PlusCircle, RefreshCw } from 'lucide-react';
import { IncidentList } from '@/components/incidents/IncidentList';
import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Incident } from '@/lib/types';

export default function DashboardPage() {
  const { data: incidents, isLoading, error, refetch } = useIncidents();
  
  const [view, setView] = useState<'grid' | 'table'>('grid');
  
  const typedIncidents: Incident[] = incidents || [];

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
          <p className="text-muted-foreground mt-2">
            Monitor and manage automated incident resolutions.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2 text-right">
           <div className="flex gap-2">
              {[
                { name: 'SNT', color: 'bg-emerald-500' },
                { name: 'DET', color: 'bg-blue-500' },
                { name: 'RSN', color: 'bg-purple-500' },
                { name: 'VRF', color: 'bg-orange-500' }
              ].map(agent => (
                <div key={agent.name} className="flex items-center gap-1.5 px-2 py-1 rounded bg-muted/50 border border-white/5">
                   <span className={`w-1.5 h-1.5 rounded-full ${agent.color} animate-pulse`} />
                   <span className="text-[10px] font-bold text-muted-foreground">{agent.name}</span>
                </div>
              ))}
           </div>
           <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Autonomous Pipeline Active</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading} className="h-14 font-bold border-white/5 bg-muted/20 hover:bg-muted/30">
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Assets
          </Button>
          <Button asChild className="h-14 font-bold bg-cyan-600 hover:bg-cyan-500 text-white border-0 shadow-[0_0_20px_rgba(6,182,212,0.2)]">
            <Link href="/incidents/create">
              <PlusCircle className="w-4 h-4 mr-2" />
              New Incident
            </Link>
          </Button>
      </div>

      <Tabs defaultValue="grid" value={view} onValueChange={(v) => setView(v as 'grid' | 'table')}>
        <div className="flex justify-between items-center mb-4">
          <TabsList>
            <TabsTrigger value="grid">Grid View</TabsTrigger>
            <TabsTrigger value="table">List View</TabsTrigger>
          </TabsList>
        </div>


        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 rounded-xl bg-muted/50 animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="p-8 rounded-lg border border-red-200 bg-red-50 text-red-800 text-center">
            <p>Failed to load incidents. Please try again.</p>
            <Button variant="outline" onClick={() => refetch()} className="mt-4">Retry</Button>
          </div>
        ) : !typedIncidents.length ? (
            <div className="text-center py-20 bg-muted/20 rounded-xl border border-dashed">
                <h3 className="text-lg font-medium">No incidents found</h3>
                <p className="text-muted-foreground mt-1 mb-6">Create your first incident to get started.</p>
                <Button asChild>
                    <Link href="/incidents/create">Create Incident</Link>
                </Button>
            </div>
        ) : (
          <>
            <TabsContent value="grid" className="mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {typedIncidents.map((incident) => (
                  <IncidentCard key={incident.id} incident={incident} />
                ))}
              </div>
            </TabsContent>
            <TabsContent value="table" className="mt-0">
               <IncidentList incidents={typedIncidents} />
            </TabsContent>
          </>
        )}
      </Tabs>
    </div>
  );
}
