import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  checkHealth,
  createIncident,
  CreateIncidentPayload,
  fetchIncidents,
  getIncident,
  retryIncident,
  getDetectiveReport,
  getReasonerOutput,
  getVerifierOutput,
} from '@/lib/api';

export const useIncidents = (status?: string, severity?: string) => {
  return useQuery({
    queryKey: ['incidents', status, severity],
    queryFn: () => fetchIncidents(status, severity),
    refetchInterval: 5000, // Poll every 5 seconds for updates
  });
};

export const useIncident = (id: string) => {
  return useQuery({
    queryKey: ['incident', id],
    queryFn: () => getIncident(id),
    refetchInterval: 3000, // Poll faster for detailed view
    enabled: !!id,
  });
};

export const useCreateIncident = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateIncidentPayload) => createIncident(payload),
    onSuccess: () => {
      toast.success('Incident created successfully');
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to create incident: ${error.message}`);
    },
  });
};

export const useRetryIncident = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => retryIncident(id),
    onSuccess: (data) => {
      toast.success('Retry initiated');
      queryClient.invalidateQueries({ queryKey: ['incident', data.id] });
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to retry incident: ${error.message}`);
    },
  });
};

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    refetchInterval: 30000,
  });
};

export const useDetectiveReport = (id: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['incident-detective', id],
    queryFn: () => getDetectiveReport(id),
    enabled: enabled && !!id,
    refetchInterval: (data) => (data ? false : 3000), // Poll until data is found
  });
};

export const useReasonerOutput = (id: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['incident-reasoner', id],
    queryFn: () => getReasonerOutput(id),
    enabled: enabled && !!id,
    refetchInterval: (data) => (data ? false : 3000),
  });
};

export const useVerifierOutput = (id: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['incident-verifier', id],
    queryFn: () => getVerifierOutput(id),
    enabled: enabled && !!id,
    refetchInterval: (data) => (data ? false : 3000),
  });
};
