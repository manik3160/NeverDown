import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Incident, IncidentStatus } from '@/lib/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/incidents/StatusBadge';
import { SeverityBadge } from '@/components/incidents/SeverityBadge';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import { GitBranch, Github, ArrowRight } from 'lucide-react';

interface IncidentCardProps {
  incident: Incident;
}

export function IncidentCard({ incident }: IncidentCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold line-clamp-1">
              {incident.title}
            </CardTitle>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Github className="w-3.5 h-3.5" />
              <span>{incident.metadata?.repository?.url?.split('/').slice(-2).join('/') || 'No repository'}</span>
              {incident.metadata?.repository?.branch && (
                <>
                  <Badge variant="secondary" className="text-xs h-5 px-1.5 font-normal">
                    <GitBranch className="w-3 h-3 mr-1" />
                    {incident.metadata?.repository?.branch}
                  </Badge>
                </>
              )}
            </div>
          </div>
          <StatusBadge status={incident.status} />
        </div>
      </CardHeader>
      <CardContent className="pb-3 text-sm text-muted-foreground line-clamp-2 min-h-[4rem]">
        {incident.description || 'No description provided.'}
        {incident.current_state && incident.status !== IncidentStatus.COMPLETED && incident.status !== IncidentStatus.FAILED && (
          <div className="mt-2 flex items-center gap-2 text-xs text-cyan-600 font-medium animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
            {incident.current_state}...
          </div>
        )}
      </CardContent>
      <CardFooter className="pt-0 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <SeverityBadge severity={incident.severity} />
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}
          </span>
        </div>
        <Button asChild variant="ghost" size="sm" className="gap-1 hover:bg-muted/50">
          <Link href={`/incidents/${incident.id}`}>
            View Details <ArrowRight className="w-4 h-4" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
