'use client';

import { TestOutcome, TestResult, VerificationResult, VerificationStatus } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckCircle, XCircle, AlertCircle, Clock, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VerifierViewProps {
  verifierData?: VerificationResult;
  isLoading: boolean;
}

export function VerifierView({ verifierData, isLoading }: VerifierViewProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-muted-foreground bg-muted/10 rounded-lg border border-dashed animate-pulse">
        <Zap className="w-8 h-8 mb-4 animate-bounce text-yellow-500" />
        <p>Running verification tests in sandbox...</p>
      </div>
    );
  }

  if (!verifierData) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-muted-foreground bg-muted/10 rounded-lg border border-dashed">
        <CheckCircle className="w-8 h-8 mb-4 opacity-50" />
        <p>No verification results available yet.</p>
      </div>
    );
  }

  const statusColor = {
    [VerificationStatus.PASSED]: 'text-green-600 bg-green-500/10 border-green-200',
    [VerificationStatus.FAILED]: 'text-red-600 bg-red-500/10 border-red-200',
    [VerificationStatus.NO_TESTS]: 'text-yellow-600 bg-yellow-500/10 border-yellow-200',
    [VerificationStatus.ERROR]: 'text-orange-600 bg-orange-500/10 border-orange-200',
  }[verifierData.status];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex justify-between items-center">
            <CardTitle>Verification Results</CardTitle>
            <Badge variant="outline" className={cn("text-base px-3 py-1", statusColor)}>
               {verifierData.status.toUpperCase()}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
             Passed: {verifierData.tests_passed} | Failed: {verifierData.tests_failed}
          </p>
        </CardHeader>
        <CardContent>
           {verifierData.verification_failed_reason && (
               <div className="mb-4 p-3 rounded bg-red-50/50 border border-red-100 text-red-800 text-sm">
                   <span className="font-semibold">Failure Reason:</span> {verifierData.verification_failed_reason}
               </div>
           )}

           <ScrollArea className="h-[400px] pr-4 max-w-full">
              <div className="space-y-2">
                  {verifierData.tests_run.map((test, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded border bg-card/50 hover:bg-muted/50 transition-colors">
                          <div className="flex items-center gap-3 overflow-hidden">
                              {test.outcome === TestOutcome.PASSED && <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />}
                              {test.outcome === TestOutcome.FAILED && <XCircle className="w-4 h-4 text-red-500 shrink-0" />}
                              {test.outcome === TestOutcome.SKIPPED && <Clock className="w-4 h-4 text-gray-400 shrink-0" />}
                              {test.outcome === TestOutcome.ERROR && <AlertCircle className="w-4 h-4 text-orange-500 shrink-0" />}
                              
                              <div className="min-w-0">
                                  <p className="font-medium text-sm truncate" title={test.name}>{test.name}</p>
                                  {test.error_message && (
                                      <p className="text-xs text-red-500 mt-1 line-clamp-2">{test.error_message}</p>
                                  )}
                              </div>
                          </div>
                          <span className="text-xs text-muted-foreground font-mono shrink-0 ml-2">
                              {test.duration_ms}ms
                          </span>
                      </div>
                  ))}
                  {!verifierData.tests_run.length && (
                      <p className="text-center text-muted-foreground py-8">No individual test results recorded.</p>
                  )}
              </div>
           </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
