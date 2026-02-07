'use client';

import { useForm } from 'react-hook-form';
import { useCreateIncident } from '@/hooks/useIncidents';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { IncidentSeverity, IncidentSource } from '@/lib/types';
import { useRouter } from 'next/navigation';

interface FormValues {
  title: string;
  description?: string;
  severity: string;
  branch?: string;
  repo_url: string;
  logs?: string;
}

export default function CreateIncidentPage() {
  const { register, handleSubmit, setValue } = useForm<FormValues>();
  const createIncident = useCreateIncident();
  const router = useRouter();

  const onSubmit = (data: FormValues) => {
    createIncident.mutate(
      {
        ...data,
        severity: data.severity as IncidentSeverity,
        source: IncidentSource.MANUAL,
        metadata: {
          repository: {
            url: data.repo_url,
            branch: data.branch || 'main',
          },
        },
      },
      {
        onSuccess: () => {
          router.push('/dashboard');
        },
      }
    );
  };

  return (
    <div className="container max-w-2xl py-10">
      <h1 className="text-2xl font-bold mb-6">Create New Incident</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input id="title" {...register('title', { required: true })} placeholder="e.g. Backend API Timing Out" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description (Optional)</Label>
          <Textarea
            id="description"
            {...register('description')}
            placeholder="Describe the issue..."
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="severity">Severity</Label>
            <Select onValueChange={(val) => setValue('severity', val)} defaultValue={IncidentSeverity.MEDIUM}>
              <SelectTrigger>
                <SelectValue placeholder="Select severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={IncidentSeverity.LOW}>Low</SelectItem>
                <SelectItem value={IncidentSeverity.MEDIUM}>Medium</SelectItem>
                <SelectItem value={IncidentSeverity.HIGH}>High</SelectItem>
                <SelectItem value={IncidentSeverity.CRITICAL}>Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
             <Label htmlFor="branch">Traget Branch</Label>
             <Input id="branch" {...register('branch')} placeholder="main" />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="repo_url">Repository URL</Label>
          <Input id="repo_url" {...register('repo_url', { required: true })} placeholder="https://github.com/org/repo" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="logs">Logs / Error Stack Trace</Label>
          <Textarea 
            id="logs"
            {...register('logs')}
            placeholder="Paste relevant logs here..."
            className="font-mono text-sm h-32"
          />
        </div>

        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={createIncident.isPending}>
            {createIncident.isPending ? 'Creating...' : 'Create Incident'}
          </Button>
        </div>
      </form>
    </div>
  );
}
