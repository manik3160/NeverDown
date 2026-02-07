import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { Incident } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import { SeverityBadge } from "./SeverityBadge";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface IncidentListProps {
  incidents: Incident[];
}

export function IncidentList({ incidents }: IncidentListProps) {
  if (!incidents.length) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center border rounded-lg bg-muted/40">
        <p className="text-muted-foreground">No incidents found.</p>
        <p className="text-sm text-muted-foreground mt-1">Check back later or creaete a new one.</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Severity</TableHead>
            <TableHead>Repository</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {incidents.map((incident) => (
            <TableRow key={incident.id}>
              <TableCell className="font-medium max-w-[300px] truncate">
                {incident.title}
              </TableCell>
              <TableCell>
                <StatusBadge status={incident.status} />
              </TableCell>
              <TableCell>
                <SeverityBadge severity={incident.severity} />
              </TableCell>
              <TableCell className="max-w-[200px] truncate">
                {incident.metadata.repository.url.split('/').slice(-2).join('/')}
              </TableCell>
              <TableCell className="text-muted-foreground whitespace-nowrap">
                {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}
              </TableCell>
              <TableCell className="text-right">
                <Button asChild variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <Link href={`/incidents/${incident.id}`}>
                    <ArrowRight className="h-4 w-4" />
                    <span className="sr-only">View</span>
                  </Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
