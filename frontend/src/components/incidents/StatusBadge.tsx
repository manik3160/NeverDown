import { Badge } from '@/components/ui/badge';
import { IncidentStatus } from '@/lib/types';
import { cn } from '@/lib/utils';
import { CheckCircle, Clock, AlertCircle, PlayCircle, XCircle, FileCode, CheckCheck, RefreshCcw } from 'lucide-react';

interface StatusBadgeProps {
  status: IncidentStatus;
  className?: string;
  animate?: boolean;
}

const statusConfig: Record<IncidentStatus, { label: string; color: string; icon: any }> = {
  [IncidentStatus.PENDING]: { label: 'Pending', color: 'bg-yellow-500/15 text-yellow-600 border-yellow-200', icon: Clock },
  [IncidentStatus.PROCESSING]: { label: 'Processing', color: 'bg-blue-500/15 text-blue-600 border-blue-200', icon: PlayCircle },
  [IncidentStatus.SANITIZING]: { label: 'Sanitizing', color: 'bg-blue-500/15 text-blue-600 border-blue-200', icon: FileCode },
  [IncidentStatus.ANALYZING]: { label: 'Analyzing', color: 'bg-indigo-500/15 text-indigo-600 border-indigo-200', icon: PlayCircle },
  [IncidentStatus.REASONING]: { label: 'Reasoning', color: 'bg-purple-500/15 text-purple-600 border-purple-200', icon: PlayCircle },
  [IncidentStatus.VERIFYING]: { label: 'Verifying', color: 'bg-orange-500/15 text-orange-600 border-orange-200', icon: CheckCheck },
  [IncidentStatus.CREATING_PR]: { label: 'Creating PR', color: 'bg-cyan-500/15 text-cyan-600 border-cyan-200', icon: FileCode },
  [IncidentStatus.PR_CREATED]: { label: 'PR Created', color: 'bg-green-500/15 text-green-600 border-green-200', icon: CheckCircle },
  [IncidentStatus.COMPLETED]: { label: 'Completed', color: 'bg-green-500/15 text-green-600 border-green-200', icon: CheckCircle },
  [IncidentStatus.FAILED]: { label: 'Failed', color: 'bg-red-500/15 text-red-600 border-red-200', icon: XCircle },
  [IncidentStatus.RETRYING]: { label: 'Retrying', color: 'bg-amber-500/15 text-amber-600 border-amber-200', icon: RefreshCcw },
};

export function StatusBadge({ status, className, animate = false }: StatusBadgeProps) {
  const config = statusConfig[status] || { label: status, color: 'bg-gray-100 text-gray-800', icon: Clock };
  const Icon = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn(
        'gap-1.5 py-1 px-2.5 font-medium border shadow-sm',
        config.color,
        animate && status !== IncidentStatus.COMPLETED && status !== IncidentStatus.FAILED && 'animate-pulse',
        className
      )}
    >
      <Icon className="w-3.5 h-3.5" />
      {config.label}
    </Badge>
  );
}
