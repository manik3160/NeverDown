'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('neverdown_token');
    if (!token) {
      toast.error('Session expired', { description: 'Please login to continue.' });
      router.push('/login');
    } else {
      setIsAuthenticated(true);
    }
  }, []);

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-black/95">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Optional: Add a Dashboard Navbar here */}
      <header className="border-b bg-muted/40 backdrop-blur sticky top-0 z-50">
          <div className="container flex h-14 items-center gap-4 px-4 sm:px-6">
             <div className="font-semibold text-lg flex items-center gap-2">
                 <span className="w-3 h-3 rounded-full bg-cyan-500 animate-pulse" />
                 NeverDown Console
             </div>
             <div className="ml-auto flex items-center gap-4">
                 <button 
                    onClick={() => {
                        localStorage.removeItem('neverdown_token');
                        router.push('/');
                    }}
                    className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                 >
                     Logout
                 </button>
             </div>
          </div>
      </header>
      <main className="container py-6">
        {children}
      </main>
    </div>
  );
}
