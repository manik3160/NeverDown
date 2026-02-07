'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { 
  Loader2, 
  LayoutDashboard, 
  AlertCircle, 
  Settings, 
  LogOut, 
  Terminal,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useHealth } from '@/hooks/useIncidents';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const { data: health, isLoading: isHealthLoading } = useHealth();

  useEffect(() => {
    const token = localStorage.getItem('neverdown_token');
    if (!token) {
      toast.error('Session expired', { description: 'Please login to continue.' });
      router.push('/login');
    } else {
      setIsAuthenticated(true);
    }
  }, [router]);

  const navItems = [
    { name: 'Incidents', href: '/dashboard', icon: AlertCircle },
    { name: 'Workflows', href: '#', icon: Terminal },
    { name: 'Security', href: '#', icon: ShieldCheck },
    { name: 'Settings', href: '#', icon: Settings },
  ];

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-black/95">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  const handleLogout = () => {
    localStorage.removeItem('neverdown_token');
    router.push('/');
  };



  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-muted/20 backdrop-blur hidden md:flex flex-col sticky top-0 h-screen">
        <div className="p-6 flex items-center gap-2 border-b">
          <Zap className="w-5 h-5 text-cyan-500 fill-cyan-500" />
          <span className="font-bold text-lg tracking-tight">NEVERDOWN</span>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link 
                key={item.name} 
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-primary/10 text-primary" 
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t">
          <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive" onClick={handleLogout}>
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen">
        <header className="border-b bg-background/50 backdrop-blur sticky top-0 z-50 h-16 flex items-center px-6">
          <div className="md:hidden flex items-center gap-2 mr-4">
            <Zap className="w-5 h-5 text-cyan-500" />
          </div>
          <div className="text-sm font-medium breadcrumbs">
            Dashboard / {pathname === '/dashboard' ? 'Incidents' : pathname.split('/').pop()}
          </div>
          <div className="ml-auto flex items-center gap-4">
             {isHealthLoading ? (
               <div className="text-xs text-muted-foreground">Checking health...</div>
             ) : health?.status === 'healthy' ? (
               <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-xs text-green-500 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  Systems Operational
               </div>
             ) : (
               <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-xs text-red-500 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                  API Disconnected
               </div>
             )}
          </div>
        </header>
        
        <main className="flex-1 p-6 md:p-8 lg:p-10 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
