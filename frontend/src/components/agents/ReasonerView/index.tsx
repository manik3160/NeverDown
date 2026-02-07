'use client';

import React from 'react';
import DiffViewer from 'react-diff-viewer-continued';
import ReactMarkdown from 'react-markdown';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertTriangle, CheckCircle, FileCode } from 'lucide-react';
import { ReasonerOutput } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Separator } from '@/components/ui/separator';

interface ReasonerViewProps {
  reasonerData?: ReasonerOutput;
  isLoading?: boolean;
}

export function ReasonerView({ reasonerData, isLoading }: ReasonerViewProps) {

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-muted-foreground bg-muted/10 rounded-lg border border-dashed">
        <Loader2 className="w-8 h-8 animate-spin mb-4 text-primary" />
        <p className="font-medium">Analyzing root cause & generating fix...</p>
        <p className="text-sm mt-1">Our AI is reasoning through potential solutions.</p>
      </div>
    );
  }

  if (!reasonerData) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-muted-foreground bg-muted/10 rounded-lg border border-dashed">
        <FileCode className="w-8 h-8 mb-4 opacity-50" />
        <p className="font-medium">No analysis available yet.</p>
        <p className="text-sm mt-1">The reasoner agent has not processed this incident.</p>
      </div>
    );
  }

  const confidencePercentage = Math.round(reasonerData.confidence * 100);
  let confidenceColor = "bg-red-500";
  if (confidencePercentage > 75) confidenceColor = "bg-green-500";
  else if (confidencePercentage > 50) confidenceColor = "bg-yellow-500";

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Root Cause Analysis Card */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
                <CardTitle className="text-xl flex items-center gap-2">
                    Root Cause Analysis
                </CardTitle>
                <CardDescription className="mt-1">
                    AI-generated explanation of the issue.
                </CardDescription>
            </div>
            <Badge variant="outline" className={cn("text-sm px-3 py-1 gap-2", confidenceColor.replace("bg-", "border-").replace("500", "200"), "bg-opacity-10")}>
              <span className={cn("w-2 h-2 rounded-full", confidenceColor)} />
              Confidence: {confidencePercentage}%
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="prose proze-zinc dark:prose-invert max-w-none text-sm leading-relaxed">
          <ReactMarkdown>{reasonerData.detailed_explanation}</ReactMarkdown>
        </CardContent>
      </Card>

      {/* Assumptions & Risks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {reasonerData.assumptions.length > 0 && (
            <Card>
                <CardHeader className="pb-3">
                    <CardTitle className="text-base font-medium flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-blue-500" />
                        Key Assumptions
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
                        {reasonerData.assumptions.map((assumption, i) => (
                            <li key={i}>{assumption}</li>
                        ))}
                    </ul>
                </CardContent>
            </Card>
          )}

          {reasonerData.risk_assessment && (
            <Card className="border-orange-200 bg-orange-50/50 dark:bg-orange-950/20">
                <CardHeader className="pb-3">
                    <CardTitle className="text-base font-medium flex items-center gap-2 text-orange-700 dark:text-orange-400">
                        <AlertTriangle className="w-4 h-4" />
                        Risk Assessment
                    </CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-orange-800 dark:text-orange-300">
                    <ReactMarkdown>{reasonerData.risk_assessment}</ReactMarkdown>
                </CardContent>
            </Card>
          )}
      </div>

      {/* Proposed Patch Diff */}
      <Card className="overflow-hidden border-2 border-primary/10 shadow-lg">
        <CardHeader className="bg-muted/30 border-b pb-4">
           <CardTitle className="flex items-center gap-2">
               <FileCode className="w-5 h-5 text-primary" />
               Proposed Fix
           </CardTitle>
           <CardDescription>
               Review the generated patch before it is applied.
           </CardDescription>
        </CardHeader>
        <CardContent className="p-0 bg-[#2d2d2d]">
           <DiffViewer 
             oldValue={''} 
             newValue={reasonerData.patch.diff} 
             splitView={false} 
             useDarkTheme={true} 
             hideLineNumbers={false}
             showDiffOnly={false}
             styles={{
                 variables: {
                     dark: {
                         diffViewerBackground: '#2d2d2d',
                         diffViewerColor: '#FFF',
                         addedBackground: '#044B53',
                         addedColor: 'white',
                         removedBackground: '#632F34',
                         removedColor: 'white',
                         wordAddedBackground: '#055d67',
                         wordRemovedBackground: '#7d383f',
                     }
                 },
                 line: {
                     padding: '10px 2px',
                     '&:hover': {
                         background: '#383838',
                     },
                 } 
             }}
           />
        </CardContent>
      </Card>
    </div>
  );
}
