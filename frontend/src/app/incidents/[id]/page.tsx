'use client';

import { useIncident, useRetryIncident, useDetectiveReport, useReasonerOutput, useVerifierOutput } from "@/hooks/useIncidents";
import { useParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { DetectiveView } from "@/components/agents/DetectiveView";
import { ReasonerView } from "@/components/agents/ReasonerView";
import { VerifierView } from "@/components/agents/VerifierView";
import { StatusBadge } from "@/components/incidents/StatusBadge";
import { SeverityBadge } from "@/components/incidents/SeverityBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, RefreshCw, GitBranch, Github, ExternalLink, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { IncidentStatus } from "@/lib/types";
import { Timeline } from "@/components/incidents/Timeline";

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: incident, isLoading, error, refetch } = useIncident(id);
  const retryIncident = useRetryIncident();
  const queryClient = useQueryClient();

  const { data: detectiveReport, isLoading: isDetectiveLoading } = useDetectiveReport(id as string);
  const { data: reasonerOutput, isLoading: isReasonerLoading } = useReasonerOutput(id as string);
  const { data: verifierOutput, isLoading: isVerifierLoading } = useVerifierOutput(id as string);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 min-h-[50vh]">
        <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground animate-pulse">Loading incident details...</p>
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="container py-20 text-center">
        <h2 className="text-2xl font-bold text-red-600 mb-2">Error Loading Incident</h2>
        <p className="text-muted-foreground mb-6">Could not fetch incident details. It may not exist or the backend is unreachable.</p>
        <Button onClick={() => refetch()}>Try Again</Button>
      </div>
    );
  }

  const handleRetry = () => {
    retryIncident.mutate(incident.id);
  };

  // Extract agent data from timeline or separate endpoint effectively
  // For MVP, we assume the backend might serve this joined, or we parse it from the incident structure if available
  // In a real app, you might fetch specific agent reports (detective_report, reasoner_output) via separate API calls
  // dependent on the current status.
  // BUT for this implementation plan, we will assume we need to fetch them or they are part of a 'full' incident object.
  // The current `Incident` interface in `types.ts` doesn't explicitly have `detective_report` etc.
  // We should update the backend/types to include these or fetch them separately.
  // For now, let's assume we can add them to the type and the backend provides them.

  // NOTE: The backend `IncidentResponse` doesn't seem to include the full reports.
  // In a real scenario, we'd add endpoints like /incidents/{id}/detective, etc.
  // Let's stub this behavior or add 'mock' data access if the fields are missing.
  
  // Actually, we can just use the status to show "Pending..." or "Done" in the tabs for now
  // or duplicate the `analysis` table data into the incident response.
  
  // Let's just pass `undefined` if missing and let the components handle "No data yet".
  
  return (
    <div className="container mx-auto py-8 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold tracking-tight">{incident.title}</h1>
            <StatusBadge status={incident.status} animate={true} />
          </div>
          <p className="text-muted-foreground max-w-2xl">{incident.description}</p>
        </div>
        <div className="flex gap-3">
          {incident.status === IncidentStatus.FAILED && (
            <Button variant="outline" onClick={handleRetry} disabled={retryIncident.isPending}>
              <RefreshCw className={`w-4 h-4 mr-2 ${retryIncident.isPending ? 'animate-spin' : ''}`} />
              Retry Analysis
            </Button>
          )}
          {incident.pr_url && (
            <Button asChild className="gap-2">
              <a href={incident.pr_url} target="_blank" rel="noopener noreferrer">
                <Github className="w-4 h-4" />
                View Pull Request
                <ExternalLink className="w-3 h-3 opacity-50" />
              </a>
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main Content (Tabs) */}
        <div className="lg:col-span-3 space-y-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-wrap gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Github className="w-4 h-4 text-muted-foreground" />
                  <span className="font-medium text-foreground">{incident.metadata?.repository?.url || 'No URL'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <GitBranch className="w-4 h-4 text-muted-foreground" />
                  <span className="font-medium text-foreground">{incident.metadata?.repository?.branch || 'main'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={incident.severity} />
                </div>
                <div className="flex items-center gap-2 text-muted-foreground ml-auto">
                    <Clock className="w-4 h-4" />
                    Created {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="detective" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="detective">1. Detective (Analysis)</TabsTrigger>
              <TabsTrigger value="reasoner">2. Reasoner (Fix)</TabsTrigger>
              <TabsTrigger value="verifier">3. Verifier (Test)</TabsTrigger>
            </TabsList>
            
            <TabsContent value="detective" className="mt-6">
               <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Error Analysis & Suspects</h3>
                  <DetectiveView detectiveData={detectiveReport} isLoading={isDetectiveLoading || incident.status === IncidentStatus.ANALYZING} />
               </div>
            </TabsContent>
            
            <TabsContent value="reasoner" className="mt-6">
                <div className="space-y-4">
                   <h3 className="text-lg font-semibold">Root Cause & Patch</h3>
                   <ReasonerView reasonerData={reasonerOutput} isLoading={isReasonerLoading || incident.status === IncidentStatus.REASONING} />
                </div>
            </TabsContent>
            
            <TabsContent value="verifier" className="mt-6">
                 <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Verification Results</h3>
                    <VerifierView verifierData={verifierOutput?.result} isLoading={isVerifierLoading || incident.status === IncidentStatus.VERIFYING} />
                 </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Sidebar (Timeline & Meta) */}
        <div className="space-y-6">
           <Card>
               <CardHeader>
                   <CardTitle className="text-base">Live Status</CardTitle>
               </CardHeader>
               <CardContent>
                   <Timeline events={incident.timeline} currentStatus={incident.status} />
               </CardContent>
           </Card>
        </div>
      </div>
    </div>
  );
}
