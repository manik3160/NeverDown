'use client';

import { DetectiveReport } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertCircle, FileSearch, Code, Bug } from 'lucide-react';
import { Separator } from '@/components/ui/separator';

interface DetectiveViewProps {
  detectiveData?: DetectiveReport;
  isLoading: boolean;
}

export function DetectiveView({ detectiveData, isLoading }: DetectiveViewProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-muted-foreground bg-muted/10 rounded-lg border border-dashed animate-pulse">
        <FileSearch className="w-8 h-8 mb-4 animate-bounce" />
        <p>Scanning codebase & analyzing logs...</p>
      </div>
    );
  }

  if (!detectiveData) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-muted-foreground bg-muted/10 rounded-lg border border-dashed">
        <Bug className="w-8 h-8 mb-4 opacity-50" />
        <p>No detective report available yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              Identified Errors
            </CardTitle>
            <CardDescription>
              Exceptions and errors extracted from logs.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px] w-full rounded-md border p-4 bg-muted/30">
              {detectiveData.errors.map((error, i) => (
                <div key={i} className="mb-6 last:mb-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="destructive" className="font-mono text-xs">
                      {error.error_type}
                    </Badge>
                    {error.file_path && (
                      <span className="text-xs text-muted-foreground font-mono">
                        {error.file_path}:{error.line_number}
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium mb-2">{error.message}</p>
                  {error.stack_trace && (
                    <pre className="bg-black/80 text-green-400 p-3 rounded text-xs overflow-x-auto whitespace-pre-wrap font-mono border border-green-900/30">
                      {error.stack_trace}
                    </pre>
                  )}
                  {i < detectiveData.errors.length - 1 && <Separator className="my-4" />}
                </div>
              ))}
              {!detectiveData.errors.length && (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No specific errors identified in logs.
                </p>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="w-5 h-5 text-blue-500" />
              Suspected Files
            </CardTitle>
            <CardDescription>
              Files likely containing the bug.
            </CardDescription>
          </CardHeader>
          <CardContent>
             <ScrollArea className="h-[300px] pr-4">
                {detectiveData.suspected_files.map((file, i) => (
                  <div key={i} className="mb-4 last:mb-0 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
                    <div className="flex justify-between items-start mb-1">
                      <p className="font-mono text-sm font-semibold truncate hover:text-clip" title={file.path}>
                        {file.path.split('/').pop()}
                      </p>
                      <Badge variant="outline" className={file.confidence > 0.7 ? "border-green-500 text-green-500" : "border-yellow-500 text-yellow-500"}>
                        {Math.round(file.confidence * 100)}%
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2 truncate" title={file.path}>
                        {file.path}
                    </p>
                    <div className="flex flex-wrap gap-1">
                       {file.line_numbers.map(line => (
                           <Badge key={line} variant="secondary" className="text-[10px] px-1 h-5">
                               Line {line}
                           </Badge>
                       ))}
                    </div>
                  </div>
                ))}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
            <CardTitle>Evidence & Context</CardTitle>
        </CardHeader>
        <CardContent>
             <ul className="list-disc pl-5 space-y-2 text-sm text-muted-foreground">
                 {detectiveData.evidence.map((evidence, i) => (
                     <li key={i}>{evidence}</li>
                 ))}
                 {!detectiveData.evidence.length && <li>No additional context provided.</li>}
             </ul>
        </CardContent>
      </Card>
    </div>
  );
}
