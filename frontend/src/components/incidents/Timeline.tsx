import { IncidentStatus, TimelineEvent } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";
import { CheckCircle, Clock, FileCode, PlayCircle, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface TimelineProps {
  events: TimelineEvent[];
  currentStatus: IncidentStatus;
}

const statusSteps = [
  { status: IncidentStatus.PENDING, label: "Started", icon: Clock },
  { status: IncidentStatus.PROCESSING, label: "Processing", icon: PlayCircle },
  { status: IncidentStatus.SANITIZING, label: "Sanitized", icon: ShieldAlert },
  { status: IncidentStatus.ANALYZING, label: "Analyzed", icon: PlayCircle },
  { status: IncidentStatus.REASONING, label: "Patched", icon: FileCode },
  { status: IncidentStatus.VERIFYING, label: "Verified", icon: CheckCircle },
  { status: IncidentStatus.PR_CREATED, label: "PR Created", icon: CheckCircle },
];

export function Timeline({ events, currentStatus }: TimelineProps) {
  // Simple vertical timeline of events
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6 px-2">
        {statusSteps.map((step) => {
          const Icon = step.icon;
          const isActive = step.status === currentStatus;
          const isPast = events.some(e => e.state === step.status);
          
          return (
            <div key={step.status} className={cn("flex flex-col items-center gap-2", isActive ? "text-primary" : isPast ? "text-muted-foreground" : "text-muted-foreground/30")}>
              <div className={cn("p-2 rounded-full border", isActive ? "bg-primary/10 border-primary" : "bg-muted border-transparent")}>
                <Icon className="w-4 h-4" />
              </div>
              <span className="text-xs font-medium">{step.label}</span>
            </div>
          );
        })}
      </div>

      <div className="relative border-l-2 border-muted pl-6 space-y-8">
        {events.map((event, idx) => (
          <div key={idx} className="relative">
            <span className="absolute -left-[29px] top-1 h-3 w-3 rounded-full bg-primary ring-4 ring-background" />
            
            <div className="flex flex-col">
              <span className="text-sm font-medium">{event.state}</span>
              <span className="text-xs text-muted-foreground">
                {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
              </span>
              {event.details && (
                 <pre className="mt-2 text-[10px] bg-muted p-2 rounded overflow-x-auto max-w-full">
                    {JSON.stringify(event.details, null, 2)}
                 </pre>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
