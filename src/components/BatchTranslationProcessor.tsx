import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Play, 
  Pause, 
  Square, 
  Download, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Zap,
  FileText,
  Package,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  Settings,
  Eye,
  GitBranch
} from 'lucide-react';
import { toast } from 'sonner';
import { SQLFile } from './MultiFileSQLInput';
import { sqlTranslationEngine, BatchTranslationResult, TranslationResult } from '@/lib/sqlTranslationEngine';

export interface BatchJob {
  id: string;
  name: string;
  files: SQLFile[];
  targetDialect: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'error' | 'cancelled';
  progress: number;
  currentFile: string;
  startTime?: Date;
  endTime?: Date;
  results?: BatchTranslationResult;
  error?: string;
  estimatedTimeRemaining?: string;
}

interface BatchTranslationProcessorProps {
  files: SQLFile[];
  targetDialect: string;
  onTranslationComplete?: (results: BatchTranslationResult) => void;
  onDownloadReady?: (jobId: string) => void;
}

const BatchTranslationProcessor: React.FC<BatchTranslationProcessorProps> = ({
  files,
  targetDialect,
  onTranslationComplete,
  onDownloadReady
}) => {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [activeJob, setActiveJob] = useState<string | null>(null);
  const [selectedJobResults, setSelectedJobResults] = useState<BatchTranslationResult | null>(null);
  const [processingQueue, setProcessingQueue] = useState<string[]>([]);

  // Create new batch job
  const createBatchJob = useCallback(() => {
    if (files.length === 0) {
      toast.error('No files selected for translation');
      return;
    }

    const readyFiles = files.filter(f => f.status === 'ready');
    if (readyFiles.length === 0) {
      toast.error('No files are ready for translation');
      return;
    }

    const jobId = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newJob: BatchJob = {
      id: jobId,
      name: `${targetDialect.toUpperCase()} Migration - ${new Date().toLocaleTimeString()}`,
      files: readyFiles,
      targetDialect,
      status: 'pending',
      progress: 0,
      currentFile: ''
    };

    setJobs(prev => [newJob, ...prev]);
    toast.success('Batch translation job created', {
      description: `${readyFiles.length} files queued for translation to ${targetDialect.toUpperCase()}`
    });

    return jobId;
  }, [files, targetDialect]);

  // Start batch translation
  const startBatchTranslation = useCallback(async (jobId: string) => {
    const job = jobs.find(j => j.id === jobId);
    if (!job || job.status !== 'pending') return;

    setActiveJob(jobId);
    setJobs(prev => prev.map(j => 
      j.id === jobId 
        ? { ...j, status: 'running', startTime: new Date() }
        : j
    ));

    try {
      const results = await sqlTranslationEngine.translateBatch(
        job.files,
        job.targetDialect,
        (progress, currentFile) => {
          setJobs(prev => prev.map(j => 
            j.id === jobId 
              ? { 
                  ...j, 
                  progress, 
                  currentFile,
                  estimatedTimeRemaining: calculateTimeRemaining(progress, j.startTime)
                }
              : j
          ));
        }
      );

      setJobs(prev => prev.map(j => 
        j.id === jobId 
          ? { 
              ...j, 
              status: 'completed', 
              progress: 100, 
              endTime: new Date(),
              results,
              estimatedTimeRemaining: '0s'
            }
          : j
      ));

      setActiveJob(null);
      onTranslationComplete?.(results);
      onDownloadReady?.(jobId);

      toast.success('Batch translation completed!', {
        description: `${results.files.length} files translated successfully`
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Translation failed';
      setJobs(prev => prev.map(j => 
        j.id === jobId 
          ? { 
              ...j, 
              status: 'error', 
              error: errorMessage,
              endTime: new Date()
            }
          : j
      ));
      
      setActiveJob(null);
      toast.error('Batch translation failed', {
        description: errorMessage
      });
    }
  }, [jobs, onTranslationComplete, onDownloadReady]);

  // Pause job
  const pauseJob = useCallback((jobId: string) => {
    setJobs(prev => prev.map(j => 
      j.id === jobId && j.status === 'running'
        ? { ...j, status: 'paused' }
        : j
    ));
    setActiveJob(null);
    toast.info('Translation job paused');
  }, []);

  // Cancel job
  const cancelJob = useCallback((jobId: string) => {
    setJobs(prev => prev.map(j => 
      j.id === jobId && (j.status === 'running' || j.status === 'paused')
        ? { ...j, status: 'cancelled', endTime: new Date() }
        : j
    ));
    setActiveJob(null);
    toast.info('Translation job cancelled');
  }, []);

  // Remove job
  const removeJob = useCallback((jobId: string) => {
    setJobs(prev => prev.filter(j => j.id !== jobId));
    if (selectedJobResults && jobs.find(j => j.id === jobId)?.results === selectedJobResults) {
      setSelectedJobResults(null);
    }
    toast.success('Job removed');
  }, [jobs, selectedJobResults]);

  // Calculate estimated time remaining
  const calculateTimeRemaining = (progress: number, startTime?: Date): string => {
    if (!startTime || progress <= 0) return 'Calculating...';
    
    const elapsed = Date.now() - startTime.getTime();
    const estimatedTotal = (elapsed / progress) * 100;
    const remaining = estimatedTotal - elapsed;
    
    if (remaining <= 0) return '0s';
    
    const seconds = Math.round(remaining / 1000);
    if (seconds < 60) return `${seconds}s`;
    
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    
    const hours = Math.round(minutes / 60);
    return `${hours}h`;
  };

  // Format duration
  const formatDuration = (startTime: Date, endTime: Date): string => {
    const duration = endTime.getTime() - startTime.getTime();
    const seconds = Math.round(duration / 1000);
    
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.round(minutes / 60);
    return `${hours}h`;
  };

  // View job results
  const viewJobResults = useCallback((job: BatchJob) => {
    if (job.results) {
      setSelectedJobResults(job.results);
    }
  }, []);

  // Download job results
  const downloadJobResults = useCallback((job: BatchJob) => {
    if (!job.results) return;

    // Create zip-like structure (simplified as concatenated files)
    let zipContent = `# ${job.name}\n# Generated: ${new Date().toISOString()}\n\n`;
    
    job.results.files.forEach(file => {
      zipContent += `\n${'='.repeat(60)}\n`;
      zipContent += `-- FILE: ${file.name}\n`;
      zipContent += `${'='.repeat(60)}\n\n`;
      zipContent += file.result.translatedContent;
      zipContent += '\n\n';
    });

    // Add summary report
    zipContent += `\n${'='.repeat(60)}\n`;
    zipContent += `-- TRANSLATION SUMMARY\n`;
    zipContent += `${'='.repeat(60)}\n\n`;
    zipContent += `Files processed: ${job.results.files.length}\n`;
    zipContent += `Target dialect: ${job.targetDialect.toUpperCase()}\n`;
    zipContent += `Dependency order: ${job.results.dependencyOrder.join(' -> ')}\n`;
    zipContent += `Global warnings: ${job.results.globalWarnings.length}\n\n`;

    if (job.results.globalWarnings.length > 0) {
      zipContent += 'GLOBAL WARNINGS:\n';
      job.results.globalWarnings.forEach((warning, index) => {
        zipContent += `${index + 1}. ${warning}\n`;
      });
    }

    const blob = new Blob([zipContent], { type: 'text/sql' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${job.targetDialect}_migration_${new Date().toISOString().split('T')[0]}.sql`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast.success('Translation results downloaded!');
  }, []);

  // Auto-create job when files change
  useEffect(() => {
    if (files.length > 0 && jobs.length === 0) {
      createBatchJob();
    }
  }, [files, jobs.length, createBatchJob]);

  return (
    <div className="space-y-6">
      <Card className="enterprise-card">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <Package className="h-5 w-5 mr-2" />
              Batch Translation Processor
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={createBatchJob}
                disabled={files.length === 0}
              >
                <GitBranch className="h-4 w-4 mr-1" />
                New Job
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Process multiple SQL files with real-time progress tracking and batch optimization
          </CardDescription>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <div className="text-center p-8 text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium mb-2">No Translation Jobs</p>
              <p className="text-sm">
                Upload SQL files to create your first batch translation job
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Active Job Status */}
              {activeJob && (
                <Alert className="border-primary">
                  <Clock className="h-4 w-4" />
                  <AlertDescription>
                    Translation in progress: {jobs.find(j => j.id === activeJob)?.currentFile}
                  </AlertDescription>
                </Alert>
              )}

              {/* Jobs List */}
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {jobs.map(job => (
                    <Card key={job.id} className="border border-border/50">
                      <CardContent className="p-4">
                        <div className="space-y-3">
                          {/* Job Header */}
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-medium">{job.name}</h4>
                              <p className="text-sm text-muted-foreground">
                                {job.files.length} files → {job.targetDialect.toUpperCase()}
                              </p>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <Badge variant={
                                job.status === 'completed' ? 'default' :
                                job.status === 'running' ? 'secondary' :
                                job.status === 'error' ? 'destructive' :
                                job.status === 'cancelled' ? 'outline' :
                                'outline'
                              }>
                                {job.status === 'running' && <RefreshCw className="h-3 w-3 mr-1 animate-spin" />}
                                {job.status === 'completed' && <CheckCircle className="h-3 w-3 mr-1" />}
                                {job.status === 'error' && <AlertTriangle className="h-3 w-3 mr-1" />}
                                {job.status.toUpperCase()}
                              </Badge>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          {(job.status === 'running' || job.status === 'paused') && (
                            <div className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span>Progress: {job.progress}%</span>
                                <span>{job.estimatedTimeRemaining || 'Calculating...'}</span>
                              </div>
                              <Progress value={job.progress} className="h-2" />
                              {job.currentFile && (
                                <p className="text-xs text-muted-foreground">
                                  Processing: {job.currentFile}
                                </p>
                              )}
                            </div>
                          )}

                          {/* Job Stats */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Files:</span>
                              <p className="font-medium">{job.files.length}</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Target:</span>
                              <p className="font-medium">{job.targetDialect.toUpperCase()}</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Started:</span>
                              <p className="font-medium">
                                {job.startTime ? job.startTime.toLocaleTimeString() : 'Not started'}
                              </p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Duration:</span>
                              <p className="font-medium">
                                {job.startTime && job.endTime 
                                  ? formatDuration(job.startTime, job.endTime)
                                  : job.startTime 
                                    ? 'Running...'
                                    : 'Not started'
                                }
                              </p>
                            </div>
                          </div>

                          {/* Error Message */}
                          {job.error && (
                            <Alert variant="destructive">
                              <AlertTriangle className="h-4 w-4" />
                              <AlertDescription>{job.error}</AlertDescription>
                            </Alert>
                          )}

                          {/* Job Actions */}
                          <div className="flex items-center justify-between pt-2 border-t">
                            <div className="flex space-x-2">
                              {job.status === 'pending' && (
                                <Button 
                                  size="sm" 
                                  onClick={() => startBatchTranslation(job.id)}
                                  className="enterprise-button-primary"
                                >
                                  <Play className="h-4 w-4 mr-1" />
                                  Start
                                </Button>
                              )}
                              
                              {job.status === 'running' && (
                                <>
                                  <Button 
                                    size="sm" 
                                    variant="outline"
                                    onClick={() => pauseJob(job.id)}
                                  >
                                    <Pause className="h-4 w-4 mr-1" />
                                    Pause
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="outline"
                                    onClick={() => cancelJob(job.id)}
                                  >
                                    <Square className="h-4 w-4 mr-1" />
                                    Cancel
                                  </Button>
                                </>
                              )}

                              {job.status === 'paused' && (
                                <Button 
                                  size="sm" 
                                  onClick={() => startBatchTranslation(job.id)}
                                >
                                  <Play className="h-4 w-4 mr-1" />
                                  Resume
                                </Button>
                              )}

                              {job.status === 'completed' && job.results && (
                                <>
                                  <Button 
                                    size="sm" 
                                    variant="outline"
                                    onClick={() => viewJobResults(job)}
                                  >
                                    <Eye className="h-4 w-4 mr-1" />
                                    View Results
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="outline"
                                    onClick={() => downloadJobResults(job)}
                                  >
                                    <Download className="h-4 w-4 mr-1" />
                                    Download
                                  </Button>
                                </>
                              )}
                            </div>

                            <Button 
                              size="sm" 
                              variant="ghost"
                              onClick={() => removeJob(job.id)}
                              disabled={job.status === 'running'}
                            >
                              Remove
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Translation Results Viewer */}
      {selectedJobResults && (
        <Card className="enterprise-card">
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Translation Results
            </CardTitle>
            <CardDescription>
              Detailed results and analysis for the completed translation job
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="summary">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="files">Files</TabsTrigger>
                <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
                <TabsTrigger value="warnings">Warnings</TabsTrigger>
              </TabsList>

              <TabsContent value="summary" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="border border-border/50">
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">{selectedJobResults.files.length}</p>
                      <p className="text-sm text-muted-foreground">Files Translated</p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border border-border/50">
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">
                        {selectedJobResults.files.reduce((sum, f) => sum + f.result.appliedRules.length, 0)}
                      </p>
                      <p className="text-sm text-muted-foreground">Rules Applied</p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border border-border/50">
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">
                        {selectedJobResults.files.reduce((sum, f) => sum + f.result.warnings.length, 0)}
                      </p>
                      <p className="text-sm text-muted-foreground">Warnings</p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border border-border/50">
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">
                        {Math.round(
                          selectedJobResults.files.reduce((sum, f) => sum + f.result.confidence, 0) / 
                          selectedJobResults.files.length
                        )}%
                      </p>
                      <p className="text-sm text-muted-foreground">Avg Confidence</p>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="files" className="space-y-4">
                <ScrollArea className="h-[300px]">
                  <div className="space-y-3">
                    {selectedJobResults.files.map(file => (
                      <Card key={file.id} className="border border-border/50">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium">{file.name}</h4>
                            <Badge variant="outline">
                              {file.result.confidence}% confidence
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Rules Applied:</span>
                              <p className="font-medium">{file.result.appliedRules.length}</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Warnings:</span>
                              <p className="font-medium">{file.result.warnings.length}</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Errors:</span>
                              <p className="font-medium">{file.result.errors.length}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="dependencies" className="space-y-4">
                <div className="space-y-4">
                  <h4 className="font-medium">Execution Order</h4>
                  <div className="flex flex-wrap items-center gap-2">
                    {selectedJobResults.dependencyOrder.map((fileName, index) => (
                      <React.Fragment key={fileName}>
                        <Badge variant="outline">{fileName}</Badge>
                        {index < selectedJobResults.dependencyOrder.length - 1 && (
                          <ArrowRight className="h-4 w-4 text-muted-foreground" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                  
                  <p className="text-sm text-muted-foreground">
                    Estimated execution time: {selectedJobResults.estimatedExecutionTime}
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="warnings" className="space-y-4">
                {selectedJobResults.globalWarnings.length > 0 ? (
                  <div className="space-y-3">
                    <h4 className="font-medium text-warning">Global Warnings</h4>
                    {selectedJobResults.globalWarnings.map((warning, index) => (
                      <Alert key={index}>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>{warning}</AlertDescription>
                      </Alert>
                    ))}
                  </div>
                ) : (
                  <div className="text-center p-8 text-muted-foreground">
                    <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="font-medium mb-2">No Global Warnings</p>
                    <p className="text-sm">
                      The translation completed without any global issues
                    </p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BatchTranslationProcessor;