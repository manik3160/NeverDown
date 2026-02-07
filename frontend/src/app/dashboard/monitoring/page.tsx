'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  BarChart3, 
  Clock, 
  ExternalLink, 
  Gauge, 
  RefreshCw, 
  Server,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';

export default function MonitoringPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // In a real app, these would come from environment variables or settings
  const GRAFANA_URL = process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:3001';
  
  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 2000);
  };

  const panels = [
    {
      title: 'Incident Frequency',
      description: 'System-wide incident detection rate over the last 24h',
      icon: BarChart3,
      // Placeholder for Grafana panel iframe
      // In production, use: `${GRAFANA_URL}/d-solo/...`
      iframeSrc: null 
    },
    {
      title: 'Agent Response Time',
      description: 'Average latency of Detective and Reasoner agents',
      icon: Clock,
      iframeSrc: null
    },
    {
      title: 'System Health (CPU/Mem)',
      description: 'Core infrastructure resource utilization',
      icon: Gauge,
      iframeSrc: null
    }
  ];

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Monitoring</h1>
          <p className="text-muted-foreground mt-2">
            Real-time telemetry and health monitoring powered by Grafana.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh Telemetry
          </Button>
          <Button asChild size="sm" className="bg-orange-600 hover:bg-orange-500">
            <a href={GRAFANA_URL} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              Open Grafana
            </a>
          </Button>
        </div>
      </div>

      {/* Global Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-emerald-500/5 border-emerald-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Pipeline Status</p>
                <p className="text-2xl font-bold">Optimal</p>
              </div>
              <div className="p-3 bg-emerald-500/10 rounded-xl">
                <CheckCircle2 className="w-6 h-6 text-emerald-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-blue-500/5 border-blue-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-blue-600 dark:text-blue-400">Active Agents</p>
                <p className="text-2xl font-bold">12 / 12</p>
              </div>
              <div className="p-3 bg-blue-500/10 rounded-xl">
                <Server className="w-6 h-6 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-amber-500/5 border-amber-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-amber-600 dark:text-amber-400">Uptime (24h)</p>
                <p className="text-2xl font-bold">99.98%</p>
              </div>
              <div className="p-3 bg-amber-500/10 rounded-xl">
                <Activity className="w-6 h-6 text-amber-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Embedded Panels Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {panels.map((panel, i) => (
          <Card key={i} className="overflow-hidden border-white/5 bg-muted/20 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="space-y-1">
                <CardTitle className="text-lg flex items-center gap-2">
                  <panel.icon className="w-4 h-4 text-cyan-500" />
                  {panel.title}
                </CardTitle>
                <CardDescription>{panel.description}</CardDescription>
              </div>
              <Badge variant="outline" className="text-[10px] uppercase font-bold tracking-widest bg-cyan-500/10 text-cyan-500 border-none">
                Live Data
              </Badge>
            </CardHeader>
            <CardContent className="h-[350px] p-0 flex flex-col items-center justify-center border-t border-white/5 bg-black/40 relative">
              {panel.iframeSrc ? (
                <iframe 
                  src={panel.iframeSrc} 
                  width="100%" 
                  height="100%" 
                  frameBorder="0"
                  className="w-full h-full"
                />
              ) : (
                <>
                  <div className="absolute inset-0 bg-grid-white/[0.02] -z-10" />
                  <div className="text-center p-8">
                    <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
                      <AlertTriangle className="w-8 h-8 text-muted-foreground" />
                    </div>
                    <p className="text-sm font-medium">Grafana Extension Required</p>
                    <p className="text-xs text-muted-foreground mt-2 max-w-[250px] mx-auto italic">
                      Configure your Grafana endpoint and panel IDs in settings to enable live visualization.
                    </p>
                    <Button variant="link" size="sm" className="mt-4 text-cyan-500" asChild>
                      <a href={GRAFANA_URL} target="_blank" rel="noopener noreferrer">Launch Grafana Externally &rarr;</a>
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Infrastructure Map Placeholder */}
      <Card className="border-white/5 bg-muted/10">
        <CardHeader>
          <CardTitle className="text-lg">Network Latency Map</CardTitle>
          <CardDescription>Global distribution of NeverDown edge nodes</CardDescription>
        </CardHeader>
        <CardContent className="h-[200px] flex items-center justify-center text-muted-foreground italic text-sm">
          Map component initializing... [Requires Mapbox API Key]
        </CardContent>
      </Card>
    </div>
  );
}
