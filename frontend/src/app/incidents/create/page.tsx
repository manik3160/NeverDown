'use client';

import { useForm } from 'react-hook-form';
import { useCreateIncident } from '@/hooks/useIncidents';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { IncidentSeverity, IncidentSource } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { 
  AlertCircle, 
  GitBranch, 
  Github, 
  FileText, 
  Terminal, 
  ChevronLeft,
  Loader2,
  Zap,
  ShieldAlert
} from 'lucide-react';
import { motion } from 'framer-motion';

interface FormValues {
  title: string;
  description?: string;
  severity: string;
  branch?: string;
  repo_url: string;
  logs?: string;
}

export default function CreateIncidentPage() {
  const { register, handleSubmit, setValue, watch } = useForm<FormValues>();
  const createIncident = useCreateIncident();
  const router = useRouter();

  const severityValue = watch('severity') || IncidentSeverity.MEDIUM;

  const onSubmit = (data: FormValues) => {
    createIncident.mutate(
      {
        ...data,
        severity: data.severity as IncidentSeverity,
        source: IncidentSource.MANUAL,
        metadata: {
          repository: {
            url: data.repo_url,
            branch: data.branch || 'main',
          },
        },
      },
      {
        onSuccess: () => {
          router.push('/dashboard');
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-[#050510] text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-cyan-600/10 rounded-full blur-[120px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none animate-pulse" style={{ animationDelay: '2s' }} />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-3xl relative z-10"
      >
        <button 
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-cyan-400 transition-colors mb-8 group"
        >
          <ChevronLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
          Back to Dashboard
        </button>

        <Card className="border-white/10 bg-black/40 backdrop-blur-2xl shadow-2xl overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500" />
          
          <CardHeader className="space-y-4 pb-8">
            <div className="flex items-center gap-3">
               <div className="p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/20">
                  <ShieldAlert className="w-6 h-6 text-cyan-400" />
               </div>
               <div>
                  <CardTitle className="text-2xl font-bold tracking-tight text-white">Report New Incident</CardTitle>
                  <CardDescription className="text-gray-400">
                    Initialize the autonomous agent pipeline for system remediation.
                  </CardDescription>
               </div>
            </div>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
              {/* Basic Info */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title" className="text-xs uppercase tracking-widest font-bold text-gray-500 flex items-center gap-2">
                    <AlertCircle className="w-3 h-3" /> Incident Title
                  </Label>
                  <Input 
                    id="title" 
                    {...register('title', { required: true })} 
                    placeholder="e.g. Memory Leak in Production API" 
                    className="bg-white/5 border-white/10 text-white placeholder:text-gray-600 h-12 focus:border-cyan-500/50 transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description" className="text-xs uppercase tracking-widest font-bold text-gray-500 flex items-center gap-2">
                    <FileText className="w-3 h-3" /> Description
                  </Label>
                  <Textarea
                    id="description"
                    {...register('description')}
                    placeholder="Briefly describe the anomalous behavior observed..."
                    className="bg-white/5 border-white/10 text-white placeholder:text-gray-600 min-h-[100px] focus:border-cyan-500/50 transition-all"
                  />
                </div>
              </div>

              {/* Infrastructure Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl bg-white/5 border border-white/5 shadow-inner">
                <div className="space-y-2">
                  <Label htmlFor="severity" className="text-xs uppercase tracking-widest font-bold text-gray-500">
                    Severity Level
                  </Label>
                  <Select onValueChange={(val) => setValue('severity', val)} defaultValue={IncidentSeverity.MEDIUM}>
                    <SelectTrigger className="bg-black/20 border-white/10 h-11 text-white">
                      <SelectValue placeholder="Select severity" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0a0a0f] border-white/10">
                      <SelectItem value={IncidentSeverity.LOW} className="text-emerald-400">Low - Minimal Impact</SelectItem>
                      <SelectItem value={IncidentSeverity.MEDIUM} className="text-blue-400">Medium - Partial Outage</SelectItem>
                      <SelectItem value={IncidentSeverity.HIGH} className="text-orange-400">High - Critical Issue</SelectItem>
                      <SelectItem value={IncidentSeverity.CRITICAL} className="text-red-500 font-bold">Critical - Full Outage</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                   <Label htmlFor="branch" className="text-xs uppercase tracking-widest font-bold text-gray-500 flex items-center gap-2">
                      <GitBranch className="w-3 h-3" /> Target Branch
                   </Label>
                   <Input 
                    id="branch" 
                    {...register('branch')} 
                    placeholder="main" 
                    className="bg-black/20 border-white/10 h-11 text-white placeholder:text-gray-600"
                   />
                </div>

                <div className="md:col-span-2 space-y-2">
                  <Label htmlFor="repo_url" className="text-xs uppercase tracking-widest font-bold text-gray-500 flex items-center gap-2">
                    <Github className="w-3 h-3" /> Repository URL
                  </Label>
                  <Input 
                    id="repo_url" 
                    {...register('repo_url', { required: true })} 
                    placeholder="https://github.com/org/repo" 
                    className="bg-black/20 border-white/10 h-11 text-white placeholder:text-gray-600"
                  />
                </div>
              </div>

              {/* Evidence */}
              <div className="space-y-2">
                <Label htmlFor="logs" className="text-xs uppercase tracking-widest font-bold text-gray-500 flex items-center gap-2">
                  <Terminal className="w-3 h-3" /> Evidence Logs / Stack Trace
                </Label>
                <div className="relative group">
                  <Textarea 
                    id="logs"
                    {...register('logs')}
                    placeholder="Paste relevant logs for the Detective Agent to analyze..."
                    className="bg-white/5 border-white/10 text-cyan-50 placeholder:text-gray-600 font-mono text-sm min-h-[160px] focus:border-cyan-500/50 transition-all"
                  />
                  <div className="absolute top-3 right-3 opacity-20 pointer-events-none group-focus-within:opacity-50 transition-opacity">
                    <Terminal className="w-5 h-5" />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4">
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground uppercase font-bold tracking-widest">
                   <Zap className="w-3 h-3 text-cyan-500 animate-pulse" />
                   AI Deployment Pending
                </div>
                <div className="flex gap-4">
                  <Button 
                    type="button" 
                    variant="ghost" 
                    onClick={() => router.back()}
                    className="text-muted-foreground hover:text-white hover:bg-white/5"
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    disabled={createIncident.isPending}
                    className="bg-white text-black hover:bg-cyan-400 hover:text-black font-bold h-12 px-8 rounded-xl transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_30px_rgba(6,182,212,0.4)]"
                  >
                    {createIncident.isPending ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Analyzing...</>
                    ) : (
                      'Initiate Resolution'
                    )}
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        <p className="mt-8 text-center text-[10px] text-gray-500 uppercase tracking-[0.2em] font-medium">
          Authorized Operation Cluster • NeverDown v1.0.0
        </p>
      </motion.div>
    </div>
  );
}
