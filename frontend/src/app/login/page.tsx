'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Github, Loader2, Zap } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const [accessCode, setAccessCode] = useState('');

  const handleLogin = (provider: string) => {
    setIsLoading(true);
    // Simulate login
    setTimeout(() => {
      // Set a mock token
      localStorage.setItem('neverdown_token', 'mock_token_123');
      toast.success('Access Granted', { description: 'Welcome to the console.' });
      router.push('/dashboard');
    }, 1500);
  };

  const verifyCode = (e: React.FormEvent) => {
    e.preventDefault();
    if (accessCode.length < 5) {
      toast.error('Invalid Access Code', { description: 'Code must be at least 5 characters.' });
      return;
    }
    handleLogin('code');
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4 relative overflow-hidden">
        {/* Background Effects */}
        <div className="absolute top-[-20%] left-[-20%] w-[70%] h-[70%] bg-cyan-900/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-[-20%] right-[-20%] w-[70%] h-[70%] bg-purple-900/10 rounded-full blur-[100px] pointer-events-none" />

        <Card className="w-full max-w-md border-white/10 bg-black/40 backdrop-blur-xl shadow-2xl">
            <CardHeader className="text-center space-y-4">
                <div className="mx-auto bg-cyan-950/30 p-3 rounded-full w-fit border border-cyan-500/20 relative group">
                    <Zap className="w-8 h-8 text-cyan-400" />
                    <div className="absolute inset-0 bg-cyan-400/20 rounded-full animate-ping opacity-20" />
                </div>
                <div className="w-full h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent relative overflow-hidden">
                    <motion.div 
                        initial={{ left: '-100%' }}
                        animate={{ left: '100%' }}
                        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                        className="absolute top-0 bottom-0 w-1/4 bg-gradient-to-r from-transparent via-cyan-400 to-transparent"
                    />
                </div>
                <div>
                    <CardTitle className="text-2xl font-bold tracking-tight text-white">Console Access</CardTitle>
                    <CardDescription className="text-gray-400">
                        Authenticate to manage infrastructure.
                    </CardDescription>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <Button 
                    variant="outline" 
                    className="w-full h-11 bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white relative"
                    onClick={() => handleLogin('github')}
                    disabled={isLoading}
                >
                    {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Github className="w-4 h-4 mr-2" />}
                    Continue with GitHub
                    {isLoading && <span className="absolute right-4 text-xs text-muted-foreground animate-pulse">Authenticating...</span>}
                </Button>
                
                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t border-white/10" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-black px-2 text-muted-foreground">Or verify with code</span>
                    </div>
                </div>

                <form onSubmit={verifyCode} className="space-y-4">
                    <Input 
                        placeholder="Enter Access Code"
                        type="password"
                        className="bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                        value={accessCode}
                        onChange={(e) => setAccessCode(e.target.value)}
                        disabled={isLoading}
                    />
                    <Button 
                        type="submit" 
                        className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
                        disabled={isLoading}
                    >
                        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verify Access'}
                    </Button>
                </form>
            </CardContent>
            <CardFooter className="justify-center">
                <p className="text-xs text-gray-500 text-center">
                    Authorized personnel only. <br /> All actions are logged and audited.
                </p>
            </CardFooter>
        </Card>
    </div>
  );
}
