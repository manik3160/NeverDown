import { Badge } from '@/components/ui/badge';
import { IncidentSeverity } from '@/lib/types';
import { cn } from '@/lib/utils';
import { ShieldAlert, AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface SeverityBadgeProps {
  severity: IncidentSeverity;
  className?: string;
}

const severityConfig: Record<IncidentSeverity, { label: string; color: string; icon: any }> = {
  [IncidentSeverity.CRITICAL]: { label: 'CRITICAL', color: 'bg-red-500 text-white border-red-600', icon: ShieldAlert },
  [IncidentSeverity.HIGH]: { label: 'High', color: 'bg-orange-500 text-white border-orange-600', icon: AlertTriangle },
  [IncidentSeverity.MEDIUM]: { label: 'Medium', color: 'bg-yellow-500 text-black border-yellow-600', icon: AlertCircle },
  [IncidentSeverity.LOW]: { label: 'Low', color: 'bg-blue-500 text-white border-blue-600', icon: Info },
};

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const config = severityConfig[severity] || { label: severity, color: 'bg-gray-500 text-white', icon: Info };
  const Icon = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn(
        'gap-1.5 py-1 px-2.5 font-bold border shadow-sm',
        config.color,
        className
      )}
    >
      <Icon className="w-3.5 h-3.5" />
      {config.label}
    </Badge>
  );
}
