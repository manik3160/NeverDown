'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  ShieldAlert, 
  Lock, 
  EyeOff, 
  Search, 
  Activity,
  History,
  AlertTriangle,
  Fingerprint
} from 'lucide-react';
import { motion } from 'framer-motion';

const securityMetrics = [
  { label: 'Secrets Redacted', value: '42', icon: EyeOff, color: 'emerald' },
  { label: 'Threats Blocked', value: '0', icon: ShieldAlert, color: 'blue' },
  { label: 'Entropy Alerts', value: '3', icon: Activity, color: 'orange' },
  { label: 'Audit Logs', value: '1.2k', icon: History, color: 'purple' },
];

export default function SecurityPage() {
  return (
    <div className="space-y-10 pb-20">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          Security Console
        </h1>
        <p className="text-muted-foreground text-lg">
          Zero-trust infrastructure monitoring and secret sanitization status.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {securityMetrics.map((metric, i) => {
          const Icon = metric.icon;
          return (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card className="border-white/5 bg-muted/20 backdrop-blur h-full overflow-hidden relative">
                <div className={`absolute -right-4 -top-4 w-20 h-20 bg-${metric.color}-500/10 rounded-full blur-2xl`} />
                <CardHeader className="pb-2">
                  <div className={`p-2 rounded-lg w-fit mb-2 bg-${metric.color}-500/10 text-${metric.color}-500`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <CardTitle className="text-3xl font-bold tracking-tight">{metric.value}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground uppercase tracking-widest font-bold">
                    {metric.label}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2 border-white/5 bg-black/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="w-5 h-5 text-cyan-400" />
              Sanitization Logs
            </CardTitle>
            <CardDescription>Recent events detected by Agent 0 (Sanitizer).</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="group p-4 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 transition-colors flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded bg-orange-500/20 text-orange-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Redacted AWS_SECRET_ACCESS_KEY</p>
                    <p className="text-[10px] text-muted-foreground uppercase mt-1">Found in build_logs_v2.txt • 2h ago</p>
                  </div>
                </div>
                <Badge variant="outline" className="border-orange-500/30 text-orange-500 text-[9px] bg-orange-500/5 uppercase font-bold">
                  Secret Redacted
                </Badge>
              </div>
            ))}
          </CardContent>
          <CardFooter className="pt-0 justify-center">
             <button className="text-xs text-muted-foreground hover:text-white transition-colors underline underline-offset-4">
                 View complete audit history
             </button>
          </CardFooter>
        </Card>

        <Card className="border-white/5 bg-gradient-to-br from-indigo-500/10 to-transparent">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Fingerprint className="w-5 h-5 text-indigo-400" />
              Active Policies
            </CardTitle>
            <CardDescription>Zero-trust enforcement rules.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-1">
               <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">Log Redaction</span>
                  <span className="text-green-500 font-bold uppercase text-[10px]">Strict</span>
               </div>
               <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full w-full bg-green-500" />
               </div>
            </div>
            
            <div className="space-y-1">
               <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">Sandbox Egress</span>
                  <span className="text-red-500 font-bold uppercase text-[10px]">Blocked</span>
               </div>
               <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full w-full bg-red-500" />
               </div>
            </div>

            <div className="space-y-1">
               <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">Entropy Threshold</span>
                  <span className="text-cyan-500 font-bold uppercase text-[10px]">0.8 bits/char</span>
               </div>
               <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full w-0.8 bg-cyan-500" style={{ width: '80%' }} />
               </div>
            </div>

            <div className="pt-4 p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/10 text-[11px] text-indigo-300 leading-relaxed italic">
                Policy: Any script that attempts unauthorized network access within the sandbox will trigger an immediate pipeline halt and incident lockdown.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
