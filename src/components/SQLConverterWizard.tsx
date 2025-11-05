import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Upload, 
  FileText, 
  Database, 
  CheckCircle, 
  AlertTriangle, 
  Download,
  RefreshCw,
  Zap,
  X,
  ArrowRight,
  Clock,
  AlertCircle,
  Trash2,
  Settings,
  BarChart,
  FileCode,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { toast } from 'sonner';

interface SQLFileData {
  id: string;
  filename: string;
  content: string;
  size: number;
  detectedDialect: string;
  confidence: number;
  manualDialect?: string; // For manual override
  status: 'ready' | 'detecting' | 'translating' | 'completed' | 'error';
  error?: string;
}

interface TranslationResult {
  filename: string;
  source_dialect: string;
  confidence: number;
  translated_sql: string;
  translation_confidence: number;
  warnings: string[];
  errors: string[];
  line_count_before: number;
  line_count_after: number;
  processing_time_ms: number;
  optimization_suggestions: string[];
}

interface BatchConversionResult {
  files: TranslationResult[];
  overall_confidence: number;
  total_processing_time_ms: number;
  success_count: number;
  failure_count: number;
}

const databases = [
  { id: 'mysql', name: 'MySQL', icon: '🐬' },
  { id: 'postgresql', name: 'PostgreSQL', icon: '🐘' },
  { id: 'sqlserver', name: 'SQL Server', icon: '🏢' },
  { id: 'oracle', name: 'Oracle', icon: '🏛️' },
  { id: 'snowflake', name: 'Snowflake', icon: '❄️' },
  { id: 'sqlite', name: 'SQLite', icon: '🗄️' }
];

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 80) return 'text-green-500';
  if (confidence >= 50) return 'text-yellow-500';
  return 'text-red-500';
};

const getConfidenceBadgeVariant = (confidence: number): 'default' | 'secondary' | 'destructive' => {
  if (confidence >= 80) return 'default';
  if (confidence >= 50) return 'secondary';
  return 'destructive';
};

export default function SQLConverterWizard() {
  // State management
  const [currentStep, setCurrentStep] = useState(1);
  const [files, setFiles] = useState<SQLFileData[]>([]);
  const [targetDB, setTargetDB] = useState('snowflake');
  const [conversionOptions, setConversionOptions] = useState({
    convertSchema: true,
    convertData: true,
    keepConstraints: true,
    optimizeCode: true,
    addComments: true
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [conversionResults, setConversionResults] = useState<BatchConversionResult | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Step 1: File upload with auto-detection
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const validFiles = acceptedFiles.filter(file => 
      file.name.endsWith('.sql') || file.name.endsWith('.ddl')
    );

    if (validFiles.length === 0) {
      toast.error('Please upload SQL or DDL files');
      return;
    }

    const newFiles: SQLFileData[] = [];

    for (const file of validFiles) {
      try {
        const content = await file.text();
        const fileData: SQLFileData = {
          id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          filename: file.name,
          content,
          size: file.size,
          detectedDialect: 'unknown',
          confidence: 0,
          status: 'detecting'
        };

        newFiles.push(fileData);
        setFiles(prev => [...prev, fileData]);

        // Detect dialect
        try {
          const response = await fetch('http://localhost:8000/migration/detect-dialect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              sql_content: content,
              filename: file.name
            })
          });

          if (response.ok) {
            const result = await response.json();
            const detection = result.data;

            setFiles(prev => prev.map(f => 
              f.id === fileData.id 
                ? { 
                    ...f, 
                    detectedDialect: detection.dialect,
                    confidence: detection.confidence,
                    status: 'ready'
                  }
                : f
            ));

            if (detection.confidence < 50) {
              toast.warning(`Low confidence for ${file.name}`, {
                description: `${detection.dialect.toUpperCase()} detected with ${detection.confidence}% confidence. You can manually override.`
              });
            } else {
              toast.success(`${file.name} detected as ${detection.dialect.toUpperCase()}`, {
                description: `${detection.confidence}% confidence`
              });
            }
          }
        } catch (error) {
          console.error('Detection failed:', error);
          setFiles(prev => prev.map(f => 
            f.id === fileData.id 
              ? { ...f, status: 'ready', detectedDialect: 'unknown', confidence: 0 }
              : f
          ));
          toast.warning(`Could not auto-detect ${file.name}`, {
            description: 'Please manually select the source database'
          });
        }
      } catch (error) {
        toast.error(`Failed to read ${file.name}`);
      }
    }

    // Auto-advance to step 2 after upload
    if (newFiles.length > 0) {
      setTimeout(() => setCurrentStep(2), 500);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.sql', '.ddl'],
      'application/sql': ['.sql']
    },
    maxSize: 50 * 1024 * 1024
  });

  // Remove file
  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    toast.success('File removed');
  };

  // Manual dialect override
  const overrideDialect = (fileId: string, newDialect: string) => {
    setFiles(prev => prev.map(f => 
      f.id === fileId 
        ? { ...f, manualDialect: newDialect, confidence: 100 }
        : f
    ));
    toast.success('Dialect override applied');
  };

  // Step 3: Execute conversion
  const executeConversion = async () => {
    if (files.length === 0) {
      toast.error('No files to convert');
      return;
    }

    setIsProcessing(true);
    setProgress(0);
    setCurrentStep(3);

    try {
      // Prepare request
      const filesData = files.map(f => ({
        filename: f.filename,
        content: f.content,
        source_dialect: f.manualDialect || f.detectedDialect
      }));

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 300);

      const response = await fetch('http://localhost:8000/migration/convert-sql-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          files: filesData,
          target_dialect: targetDB,
          conversion_options: {
            optimization_level: conversionOptions.optimizeCode ? 'standard' : 'basic',
            convert_schema: conversionOptions.convertSchema,
            convert_data: conversionOptions.convertData,
            keep_constraints: conversionOptions.keepConstraints,
            optimize_code: conversionOptions.optimizeCode
          }
        })
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (!response.ok) {
        throw new Error('Conversion failed');
      }

      const result = await response.json();
      setConversionResults(result.data);

      toast.success('Conversion completed!', {
        description: `${result.data.success_count} files converted successfully`
      });

      // Auto-advance to step 4
      setTimeout(() => setCurrentStep(4), 500);

    } catch (error) {
      console.error('Conversion error:', error);
      toast.error('Conversion failed', {
        description: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Download individual file
  const downloadFile = (result: TranslationResult) => {
    const blob = new Blob([result.translated_sql], { type: 'text/sql' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translated_${result.filename}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${result.filename}`);
  };

  // Download all files as ZIP
  const downloadAllAsZip = async () => {
    if (!conversionResults) return;

    try {
      const JSZip = (await import('jszip')).default;
      const zip = new JSZip();

      // Add converted files
      conversionResults.files.forEach(result => {
        zip.file(`translated_${result.filename}`, result.translated_sql);
      });

      // Add summary report
      const report = generateReport();
      zip.file('CONVERSION_REPORT.md', report);

      // Generate and download ZIP
      const content = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(content);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sql_conversion_${targetDB}_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('ZIP downloaded successfully');
    } catch (error) {
      console.error('ZIP creation failed:', error);
      toast.error('Failed to create ZIP file');
    }
  };

  // Generate conversion report
  const generateReport = (): string => {
    if (!conversionResults) return '';

    const avgConfidence = conversionResults.overall_confidence.toFixed(1);
    const totalTime = (conversionResults.total_processing_time_ms / 1000).toFixed(2);

    let report = `# SQL Conversion Report\n\n`;
    report += `**Generated:** ${new Date().toLocaleString()}\n`;
    report += `**Target Database:** ${targetDB.toUpperCase()}\n`;
    report += `**Files Processed:** ${conversionResults.files.length}\n`;
    report += `**Success Rate:** ${conversionResults.success_count}/${conversionResults.files.length}\n`;
    report += `**Average Confidence:** ${avgConfidence}%\n`;
    report += `**Total Processing Time:** ${totalTime}s\n\n`;

    report += `---\n\n## File Details\n\n`;

    conversionResults.files.forEach((file, index) => {
      report += `### ${index + 1}. ${file.filename}\n\n`;
      report += `- **Source:** ${file.source_dialect.toUpperCase()}\n`;
      report += `- **Detection Confidence:** ${file.confidence}%\n`;
      report += `- **Translation Confidence:** ${file.translation_confidence.toFixed(1)}%\n`;
      report += `- **Lines:** ${file.line_count_before} → ${file.line_count_after}\n`;
      report += `- **Processing Time:** ${file.processing_time_ms.toFixed(0)}ms\n`;

      if (file.warnings.length > 0) {
        report += `\n**Warnings:**\n`;
        file.warnings.forEach(w => report += `- ${w}\n`);
      }

      if (file.optimization_suggestions.length > 0) {
        report += `\n**Optimization Suggestions:**\n`;
        file.optimization_suggestions.forEach(s => report += `- ${s}\n`);
      }

      report += `\n`;
    });

    report += `---\n\n*Generated by DataFlow AI SQL Converter*\n`;

    return report;
  };

  // Render step indicator
  const renderStepIndicator = () => (
    <div className="flex items-center justify-center space-x-4 mb-8">
      {[
        { num: 1, title: 'Upload & Auto-Detect', icon: Upload },
        { num: 2, title: 'Configure Conversion', icon: Settings },
        { num: 3, title: 'Review & Execute', icon: Zap },
        { num: 4, title: 'Download & Analytics', icon: Download }
      ].map((step, index) => (
        <React.Fragment key={step.num}>
          <div 
            className={`flex flex-col items-center cursor-pointer transition-all ${
              currentStep === step.num ? 'scale-110' : 'opacity-60'
            }`}
            onClick={() => {
              if (step.num <= currentStep || (step.num === 2 && files.length > 0)) {
                setCurrentStep(step.num);
              }
            }}
          >
            <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 ${
              currentStep >= step.num 
                ? 'bg-primary text-white' 
                : 'bg-muted text-muted-foreground'
            }`}>
              {currentStep > step.num ? (
                <CheckCircle className="h-6 w-6" />
              ) : (
                <step.icon className="h-6 w-6" />
              )}
            </div>
            <p className="text-xs text-center max-w-[100px]">{step.title}</p>
          </div>
          {index < 3 && (
            <ArrowRight className={`h-5 w-5 ${
              currentStep > step.num ? 'text-primary' : 'text-muted-foreground'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  return (
    <div className="space-y-6" ref={scrollRef}>
      {/* Header */}
      <div className="neon-header">
        <h1 className="text-3xl font-bold mb-2 neon-text">SQL Converter</h1>
        <p className="text-muted-foreground">
          Convert SQL files between database dialects with AI-powered detection
        </p>
      </div>

      {/* Step Indicator */}
      {renderStepIndicator()}

      {/* Step 1: Upload & Auto-Detect */}
      {currentStep === 1 && (
        <Card className="neon-card">
          <CardHeader>
            <CardTitle className="flex items-center neon-text">
              <Upload className="h-5 w-5 mr-2 neon-glow" />
              Step 1: Upload & Auto-Detect
            </CardTitle>
            <CardDescription>
              Upload your SQL files and we'll automatically detect the source database dialect
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Upload Zone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${
                isDragActive 
                  ? 'border-cyan-500 bg-cyan-500/5 scale-105' 
                  : 'neon-border-subtle hover:border-cyan-500 hover:bg-cyan-500/5'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <div>
                <p className="text-xl font-medium mb-2">
                  {isDragActive ? 'Drop your SQL files here' : 'Drag & drop SQL files'}
                </p>
                <p className="text-muted-foreground mb-4">
                  or click to browse (.sql, .ddl files up to 50MB)
                </p>
                <Button className="neon-button">
                  <Upload className="h-4 w-4 mr-2" />
                  Browse Files
                </Button>
              </div>
            </div>

            {/* Uploaded Files */}
            {files.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">Uploaded Files ({files.length})</h3>
                  <Button variant="outline" size="sm" onClick={() => setCurrentStep(2)}>
                    Continue to Configuration
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>

                <ScrollArea className="h-[400px] border rounded-lg p-4">
                  <div className="space-y-3">
                    {files.map(file => (
                      <Card key={file.id} className="border border-border/50">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3 flex-1">
                              <FileCode className="h-5 w-5 text-primary" />
                              <div className="flex-1">
                                <p className="font-medium">{file.filename}</p>
                                <p className="text-sm text-muted-foreground">
                                  {(file.size / 1024).toFixed(1)} KB
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center space-x-2">
                              {file.status === 'detecting' ? (
                                <Badge variant="secondary">
                                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                                  Detecting...
                                </Badge>
                              ) : file.status === 'ready' ? (
                                <>
                                  <Badge 
                                    variant={getConfidenceBadgeVariant(file.confidence)}
                                    className="flex items-center space-x-1"
                                  >
                                    <Database className="h-3 w-3" />
                                    <span>{file.detectedDialect.toUpperCase()}</span>
                                    <span className="ml-1">({file.confidence}%)</span>
                                  </Badge>
                                  {file.confidence < 80 && (
                                    <Select
                                      value={file.manualDialect || file.detectedDialect}
                                      onValueChange={(value) => overrideDialect(file.id, value)}
                                    >
                                      <SelectTrigger className="h-8 w-32">
                                        <SelectValue placeholder="Override" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {databases.map(db => (
                                          <SelectItem key={db.id} value={db.id}>
                                            {db.icon} {db.name}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  )}
                                </>
                              ) : null}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeFile(file.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>

                          {file.confidence > 0 && file.confidence < 50 && (
                            <Alert className="mt-3">
                              <AlertTriangle className="h-4 w-4" />
                              <AlertDescription>
                                Low detection confidence. Consider manually selecting the source dialect.
                              </AlertDescription>
                            </Alert>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: Configure Conversion */}
      {currentStep === 2 && (
        <Card className="border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              Step 2: Configure Conversion
            </CardTitle>
            <CardDescription>
              Select target database and conversion options
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Source Summary */}
            <Card className="bg-muted/30 border-border/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Detected Source Databases</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Array.from(new Set(files.map(f => f.manualDialect || f.detectedDialect))).map(dialect => {
                    const count = files.filter(f => 
                      (f.manualDialect || f.detectedDialect) === dialect
                    ).length;
                    const avgConf = Math.round(
                      files
                        .filter(f => (f.manualDialect || f.detectedDialect) === dialect)
                        .reduce((sum, f) => sum + f.confidence, 0) / count
                    );

                    return (
                      <div key={dialect} className="flex items-center space-x-2 bg-background border rounded-lg px-3 py-2">
                        <Database className="h-4 w-4 text-primary" />
                        <span className="font-medium">{dialect.toUpperCase()}</span>
                        <Badge variant="outline" className="text-xs">
                          {count} file{count > 1 ? 's' : ''}
                        </Badge>
                        <span className={`text-xs ${getConfidenceColor(avgConf)}`}>
                          {avgConf}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Target Database Selection */}
              <Card className="border-border/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Target Database</CardTitle>
                  <CardDescription>Select the database to convert to</CardDescription>
                </CardHeader>
                <CardContent>
                  <Select value={targetDB} onValueChange={setTargetDB}>
                    <SelectTrigger className="h-12">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {databases.map(db => (
                        <SelectItem key={db.id} value={db.id}>
                          <div className="flex items-center space-x-3 py-1">
                            <span className="text-2xl">{db.icon}</span>
                            <span className="font-medium">{db.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>

              {/* Conversion Options */}
              <Card className="border-border/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Conversion Options</CardTitle>
                  <CardDescription>Customize the conversion process</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    { key: 'convertSchema', label: 'Convert table structure' },
                    { key: 'convertData', label: 'Convert data queries' },
                    { key: 'keepConstraints', label: 'Keep constraints' },
                    { key: 'optimizeCode', label: 'Optimize code' },
                    { key: 'addComments', label: 'Add migration comments' }
                  ].map(option => (
                    <div key={option.key} className="flex items-center space-x-2">
                      <Checkbox
                        id={option.key}
                        checked={conversionOptions[option.key as keyof typeof conversionOptions]}
                        onCheckedChange={(checked) => 
                          setConversionOptions(prev => ({ ...prev, [option.key]: checked }))
                        }
                      />
                      <label htmlFor={option.key} className="text-sm cursor-pointer">
                        {option.label}
                      </label>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4 border-t">
              <Button variant="outline" onClick={() => setCurrentStep(1)}>
                <ArrowRight className="h-4 w-4 mr-2 rotate-180" />
                Back to Upload
              </Button>
              <Button 
                className="bg-primary hover:bg-primary/90"
                onClick={() => setCurrentStep(3)}
                disabled={files.length === 0}
              >
                Review & Execute
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Review & Execute */}
      {currentStep === 3 && (
        <Card className="border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Zap className="h-5 w-5 mr-2" />
              Step 3: Review & Execute
            </CardTitle>
            <CardDescription>
              Review your configuration and start the conversion
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Conversion Summary */}
            <Card className="bg-primary/5 border-primary/20">
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                  <div>
                    <FileText className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <p className="text-2xl font-bold">{files.length}</p>
                    <p className="text-sm text-muted-foreground">Files to Convert</p>
                  </div>
                  <div>
                    <ArrowRight className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <p className="text-lg font-bold">{targetDB.toUpperCase()}</p>
                    <p className="text-sm text-muted-foreground">Target Database</p>
                  </div>
                  <div>
                    <Clock className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <p className="text-lg font-bold">~{files.length * 2}-{files.length * 5}s</p>
                    <p className="text-sm text-muted-foreground">Est. Processing Time</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Processing State */}
            {isProcessing && (
              <Card className="border-border/50">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">Converting Files...</h4>
                      <span className="text-2xl font-bold">{progress}%</span>
                    </div>
                    <Progress value={progress} className="h-3" />
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Processing {files.length} file{files.length > 1 ? 's' : ''}...</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4 border-t">
              <Button 
                variant="outline" 
                onClick={() => setCurrentStep(2)}
                disabled={isProcessing}
              >
                <ArrowRight className="h-4 w-4 mr-2 rotate-180" />
                Back to Configuration
              </Button>
              <Button 
                className="bg-success hover:bg-success/90"
                onClick={executeConversion}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Converting...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Start Conversion
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Download & Analytics */}
      {currentStep === 4 && conversionResults && (
        <Card className="border-2 border-success/20">
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="h-5 w-5 mr-2 text-success" />
              Step 4: Download & Analytics
            </CardTitle>
            <CardDescription>
              Conversion complete! Download your files and review analytics
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Success Summary */}
            <Card className="bg-success/5 border-success/20">
              <CardContent className="pt-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <p className="text-3xl font-bold text-success">{conversionResults.success_count}</p>
                    <p className="text-sm text-muted-foreground">Files Converted</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold">{conversionResults.overall_confidence.toFixed(1)}%</p>
                    <p className="text-sm text-muted-foreground">Avg Confidence</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold">
                      {(conversionResults.total_processing_time_ms / 1000).toFixed(1)}s
                    </p>
                    <p className="text-sm text-muted-foreground">Processing Time</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold">
                      {conversionResults.files.reduce((sum, f) => sum + f.line_count_after, 0)}
                    </p>
                    <p className="text-sm text-muted-foreground">Lines of SQL</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Download Options */}
            <Card className="border-border/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Download Options</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Button 
                    className="bg-primary hover:bg-primary/90"
                    onClick={downloadAllAsZip}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download All as ZIP
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      const report = generateReport();
                      const blob = new Blob([report], { type: 'text/markdown' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = 'conversion_report.md';
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      URL.revokeObjectURL(url);
                      toast.success('Report downloaded');
                    }}
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    Download Report
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Individual File Results */}
            <Card className="border-border/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Converted Files</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-3">
                    {conversionResults.files.map((result, index) => (
                      <Card key={index} className="border border-border/50">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <FileCode className="h-5 w-5 text-primary" />
                              <div>
                                <p className="font-medium">{result.filename}</p>
                                <p className="text-sm text-muted-foreground">
                                  {result.source_dialect.toUpperCase()} → {targetDB.toUpperCase()}
                                </p>
                              </div>
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => downloadFile(result)}
                            >
                              <Download className="h-4 w-4 mr-1" />
                              Download
                            </Button>
                          </div>

                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Confidence:</span>
                              <div className="flex items-center space-x-1">
                                <Badge variant={getConfidenceBadgeVariant(result.translation_confidence)}>
                                  {result.translation_confidence.toFixed(0)}%
                                </Badge>
                              </div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Lines:</span>
                              <p className="font-medium flex items-center space-x-1">
                                <span>{result.line_count_before} →{result.line_count_after}</span>
                                {result.line_count_after > result.line_count_before ? (
                                  <TrendingUp className="h-4 w-4 text-success" />
                                ) : result.line_count_after < result.line_count_before ? (
                                  <TrendingDown className="h-4 w-4 text-destructive" />
                                ) : null}
                              </p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Time:</span>
                              <p className="font-medium">{result.processing_time_ms.toFixed(0)}ms</p>
                            </div>
                          </div>

                          {result.warnings.length > 0 && (
                            <Alert className="mt-3">
                              <AlertTriangle className="h-4 w-4" />
                              <AlertDescription>
                                <p className="font-medium mb-1">{result.warnings.length} Warning(s):</p>
                                <ul className="text-xs space-y-1">
                                  {result.warnings.slice(0, 2).map((warning, i) => (
                                    <li key={i}>• {warning}</li>
                                  ))}
                                  {result.warnings.length > 2 && (
                                    <li>• +{result.warnings.length - 2} more...</li>
                                  )}
                                </ul>
                              </AlertDescription>
                            </Alert>
                          )}

                          {result.optimization_suggestions.length > 0 && (
                            <div className="mt-3 pt-3 border-t">
                              <p className="text-sm font-medium text-primary mb-2">
                                Optimization Suggestions:
                              </p>
                              <ul className="text-xs text-muted-foreground space-y-1">
                                {result.optimization_suggestions.slice(0, 3).map((suggestion, i) => (
                                  <li key={i}>• {suggestion}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Start New Conversion */}
            <div className="flex justify-center pt-4 border-t">
              <Button 
                variant="outline"
                onClick={() => {
                  setCurrentStep(1);
                  setFiles([]);
                  setConversionResults(null);
                  setProgress(0);
                }}
              >
                <Upload className="h-4 w-4 mr-2" />
                Start New Conversion
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
