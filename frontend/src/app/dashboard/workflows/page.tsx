'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  ShieldCheck, 
  FileSearch, 
  BrainCircuit, 
  Container, 
  GitPullRequest,
  CheckCircle2,
  Activity,
  ArrowRight
} from 'lucide-react';
import { motion } from 'framer-motion';

const pipelineStages = [
  {
    id: 'sanitizer',
    name: 'Agent 0: Sanitizer',
    description: 'Scans logs for PII and secrets before they reach the LLM.',
    icon: ShieldCheck,
    status: 'Active',
    color: 'emerald',
    stats: '15+ Patterns Detected'
  },
  {
    id: 'detective',
    name: 'Agent 1: Detective',
    description: 'Parses multi-format logs and performs git-blame analysis.',
    icon: FileSearch,
    status: 'Active',
    color: 'blue',
    stats: 'Python, JS, Node support'
  },
  {
    id: 'reasoner',
    name: 'Agent 2: Reasoner',
    description: 'Uses LLMs to identify root cause and generate a fix patch.',
    icon: BrainCircuit,
    status: 'Active',
    color: 'purple',
    stats: 'Claude 3.5 & GPT-4o'
  },
  {
    id: 'verifier',
    name: 'Agent 3: Verifier',
    description: 'Runs patches in isolated Docker sandboxes to confirm fix.',
    icon: Container,
    status: 'Active',
    color: 'orange',
    stats: 'Zero-Network Sandbox'
  },
  {
    id: 'publisher',
    name: 'Agent 4: Publisher',
    description: 'Creates human-readable Pull Requests for review.',
    icon: GitPullRequest,
    status: 'Active',
    color: 'cyan',
    stats: 'GitHub Integration'
  }
];

export default function WorkflowsPage() {
  return (
    <div className="space-y-10 pb-20">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Active Workflows</h1>
        <p className="text-muted-foreground text-lg">
          Monitor and configure the autonomous incident resolution pipeline.
        </p>
      </div>

      <div className="relative">
        {/* Animated Connector Line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500/20 via-blue-500/20 via-purple-500/20 via-orange-500/20 to-cyan-500/20 -translate-y-1/2 hidden xl:block z-0" />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 relative z-10">
          {pipelineStages.map((stage, index) => {
            const Icon = stage.icon;
            return (
              <motion.div
                key={stage.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full border-white/5 bg-muted/20 backdrop-blur hover:bg-muted/30 transition-colors group cursor-pointer">
                  <CardHeader className="space-y-4">
                    <div className={`p-3 rounded-2xl w-fit bg-${stage.color}-500/10 border border-${stage.color}-500/20 text-${stage.color}-500 group-hover:scale-110 transition-transform`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between items-center">
                        <CardTitle className="text-base font-bold">{stage.name}</CardTitle>
                        <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20 text-[10px]">
                          {stage.status}
                        </Badge>
                      </div>
                      <CardDescription className="text-xs leading-relaxed">
                        {stage.description}
                      </CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground font-medium uppercase tracking-wider">
                      <Activity className="w-3 h-3" />
                      {stage.stats}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pt-10">
          <Card className="border-cyan-500/20 bg-cyan-500/5">
              <CardHeader>
                  <CardTitle className="text-xl">Engine Performance</CardTitle>
                  <CardDescription>Real-time metrics of the autonomous pipeline.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                  <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Average Resolution Time</span>
                      <span className="font-mono font-bold">2m 45s</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: '85%' }}
                        className="bg-cyan-500 h-full"
                      />
                  </div>
                  
                  <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Successful Verifications</span>
                      <span className="font-mono font-bold text-green-500">92.4%</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: '92.4%' }}
                        className="bg-green-500 h-full"
                      />
                  </div>
              </CardContent>
          </Card>

          <Card className="border-white/5 bg-transparent overflow-hidden relative">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent" />
              <CardHeader className="relative z-10">
                  <CardTitle className="text-xl">Workflow Automation</CardTitle>
                  <CardDescription>Customize triggering rules and agent settings.</CardDescription>
              </CardHeader>
              <CardContent className="relative z-10 space-y-4">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                      Worfklows can be triggered by GitHub Webhooks, Datadog Alerts, or Sentry issues. 
                      Each stage of the pipeline can be toggled or configured for specific repositories.
                  </p>
                  <div className="flex gap-4">
                      <button className="text-sm font-medium text-purple-400 flex items-center gap-2 hover:gap-3 transition-all">
                          Configure Triggers <ArrowRight className="w-4 h-4" />
                      </button>
                  </div>
              </CardContent>
          </Card>
      </div>
    </div>
  );
}
