'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Settings as SettingsIcon, 
  Github, 
  Key, 
  Database, 
  Bell, 
  Shield,
  Loader2,
  Save,
  Cpu
} from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      toast.success('Settings updated', { description: 'Preferences have been saved successfully.' });
    }, 1200);
  };

  return (
    <div className="space-y-10 pb-20 max-w-5xl">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
        <p className="text-muted-foreground text-lg">
          Configure global environment variables and agent preferences.
        </p>
      </div>

      <Tabs defaultValue="ai" className="w-full">
        <TabsList className="grid w-full grid-cols-4 lg:w-[600px] bg-muted/20 border border-white/5">
          <TabsTrigger value="ai" className="gap-2">
            <Cpu className="w-4 h-4" /> AI Engine
          </TabsTrigger>
          <TabsTrigger value="github" className="gap-2">
            <Github className="w-4 h-4" /> Integrations
          </TabsTrigger>
          <TabsTrigger value="database" className="gap-2">
            <Database className="w-4 h-4" /> Network
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="w-4 h-4" /> Alerts
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ai" className="mt-8 space-y-6">
          <Card className="border-white/5 bg-muted/10">
            <CardHeader>
              <CardTitle>LLM Configuration</CardTitle>
              <CardDescription>Select and configure your primary reasoning model.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <Label>Primary Provider</Label>
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl border border-cyan-500/20 bg-cyan-500/5 cursor-pointer flex items-center justify-between">
                        <span className="font-medium">Anthropic (Claude 3.5)</span>
                        <div className="w-3 h-3 rounded-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
                    </div>
                    <div className="p-4 rounded-xl border border-white/5 bg-white/5 cursor-pointer flex items-center justify-between hover:bg-white/10 transition-colors">
                        <span className="font-medium">OpenAI (GPT-4o)</span>
                        <div className="w-3 h-3 rounded-full border border-white/20" />
                    </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="api_key">Provider API Key</Label>
                <div className="relative">
                  <Input 
                    id="api_key" 
                    type="password" 
                    placeholder="sk-ant-..." 
                    defaultValue="••••••••••••••••••••••••••••••"
                    className="bg-background/50 border-white/10 pr-10"
                  />
                  <Key className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                </div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold pt-1">
                  Keys are never stored on our servers. Encrypted locally only.
                </p>
              </div>
            </CardContent>
            <CardFooter className="border-t border-white/5 pt-6">
              <Button onClick={handleSave} disabled={isSaving} className="gap-2 bg-white text-black hover:bg-white/90">
                {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save AI Configuration
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="github" className="mt-8">
            <Card className="border-white/5 bg-muted/10">
                <CardHeader>
                    <CardTitle>GitHub Integration</CardTitle>
                    <CardDescription>Authorize NeverDown to create branches and PRs.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="flex items-center justify-between p-4 rounded-xl border border-white/5 bg-white/5">
                        <div className="flex items-center gap-4">
                            <div className="bg-white/10 p-2 rounded-lg">
                                <Github className="w-6 h-6" />
                            </div>
                            <div>
                                <p className="font-medium text-sm">Authenticated as <span className="text-cyan-400">@manik3160</span></p>
                                <p className="text-[11px] text-muted-foreground">Connected 14 repositories</p>
                            </div>
                        </div>
                        <Button variant="outline" size="sm" className="border-white/10 hover:bg-destructive hover:text-white transition-colors">
                            Disconnect
                        </Button>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="webhook_secret">Webhook secret</Label>
                        <Input 
                            id="webhook_secret" 
                            type="password" 
                            placeholder="Enter secret for verification"
                            className="bg-background/50 border-white/10"
                        />
                    </div>
                </CardContent>
            </Card>
        </TabsContent>

        {/* Other tabs can be empty skeletons or similar cards */}
        <TabsContent value="database" className="mt-8">
            <Card className="border-dashed border-white/20 bg-transparent">
                <CardContent className="py-12 flex flex-col items-center justify-center text-center">
                    <Database className="w-12 h-12 text-muted-foreground/30 mb-4" />
                    <p className="text-muted-foreground font-medium">Network Isolation Settings</p>
                    <p className="text-xs text-muted-foreground mt-1 max-w-xs">Configure proxy and firewall rules for the sandbox environments.</p>
                </CardContent>
            </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
