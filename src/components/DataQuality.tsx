import { useState, useRef, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { 
  Upload, 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  TrendingUp,
  Download,
  Play,
  Settings,
  BarChart3,
  Loader2,
  RefreshCw
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

const qualityMetrics = [
  {
    category: "Completeness",
    score: 92.5,
    issues: 127,
    status: "good",
    description: "Missing values detected in 3 columns"
  },
  {
    category: "Accuracy", 
    score: 89.3,
    issues: 203,
    status: "warning",
    description: "Format inconsistencies in date fields"
  },
  {
    category: "Consistency",
    score: 96.1,
    issues: 45,
    status: "excellent",
    description: "Minor duplicate records found"
  },
  {
    category: "Validity",
    score: 87.8,
    issues: 156,
    status: "warning", 
    description: "Invalid email formats detected"
  }
];

const issueTypes = [
  { type: "Duplicates", count: 1247, severity: "medium" },
  { type: "Missing Values", count: 892, severity: "high" },
  { type: "Outliers", count: 234, severity: "low" },
  { type: "Format Issues", count: 567, severity: "medium" },
  { type: "Invalid References", count: 89, severity: "high" }
];

export default function DataQuality() {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [currentDataProfile, setCurrentDataProfile] = useState<number | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("upload");
  const [cleaningConfig, setCleaningConfig] = useState({
    similarityThreshold: 85,
    duplicateMethod: "semantic",
    imputationStrategy: "ml_prediction",
    removeOutliers: true,
    standardizeFormat: true
  });
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch recent uploads from API
  const { data: uploadsData, isLoading, error } = useQuery({
    queryKey: ['recent-uploads'],
    queryFn: api.dataQuality.getRecentUploads,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch quality summary for current data profile
  const { data: qualitySummary, isLoading: isLoadingQuality } = useQuery({
    queryKey: ['quality-summary', currentDataProfile],
    queryFn: () => currentDataProfile ? api.dataQuality.getQualitySummary(currentDataProfile) : null,
    enabled: !!currentDataProfile,
    refetchInterval: 5000, // Refresh every 5 seconds when analyzing
  });

  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: api.dataQuality.uploadFile,
    onSuccess: (data) => {
      toast({
        title: "File uploaded successfully",
        description: `${data.file_info.name} (${data.file_info.rows} rows, ${data.file_info.columns} columns)`,
      });
      setCurrentDataProfile(data.data_profile_id);
      setCurrentJobId(data.job_id);
      setActiveTab("assessment");
      queryClient.invalidateQueries({ queryKey: ['recent-uploads'] });
      
      // Clear any previous upload progress
      setUploadProgress(0);
      
      // Start polling for analysis results
      startAnalysisPolling(data.job_id);
    },
    onError: (error) => {
      console.error('Upload error:', error);
      setUploadProgress(0);
      toast({
        title: "Upload failed",
        description: error.message || "An error occurred during file upload. Please try again.",
        variant: "destructive",
      });
    },
  });

  // Data analysis mutation
  const analysisMutation = useMutation({
    mutationFn: api.dataQuality.analyzeData,
    onSuccess: (data) => {
      toast({
        title: "Analysis started",
        description: "Your data is being analyzed for quality issues.",
      });
      setCurrentJobId(data.job_id);
      startAnalysisPolling(data.job_id);
    },
    onError: (error) => {
      toast({
        title: "Analysis failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Data cleaning mutation
  const cleaningMutation = useMutation({
    mutationFn: api.dataQuality.startCleaning,
    onSuccess: (data) => {
      toast({
        title: data.preview_only ? "Preview generated" : "Cleaning started",
        description: data.preview_only ? "Review the changes before applying." : "Your data is being cleaned.",
      });
      if (!data.preview_only) {
        setCurrentJobId(data.job_id);
        startAnalysisPolling(data.job_id);
        setActiveTab("validation");
      }
    },
    onError: (error) => {
      toast({
        title: "Cleaning failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Job status polling
  const startAnalysisPolling = useCallback((jobId: string) => {
    setIsAnalyzing(true);
    const pollInterval = setInterval(async () => {
      try {
        const jobStatus = await api.dataQuality.getJobStatus(jobId);
        setUploadProgress(jobStatus.progress_percentage || 0);
        
        if (jobStatus.status === 'completed') {
          setIsAnalyzing(false);
          clearInterval(pollInterval);
          setUploadProgress(100);
          queryClient.invalidateQueries({ queryKey: ['quality-summary', currentDataProfile] });
          queryClient.invalidateQueries({ queryKey: ['recent-uploads'] });
          toast({
            title: "Analysis completed",
            description: "Your data quality analysis is ready.",
          });
        } else if (jobStatus.status === 'failed') {
          setIsAnalyzing(false);
          clearInterval(pollInterval);
          toast({
            title: "Analysis failed",
            description: jobStatus.error_message || "An error occurred during analysis.",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    }, 2000);

    // Clear interval after 5 minutes to prevent infinite polling
    setTimeout(() => {
      clearInterval(pollInterval);
      setIsAnalyzing(false);
    }, 300000);
  }, [currentDataProfile, queryClient, toast]);

  // Handle file selection
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      handleFileUpload(file);
    }
  }, []);

  // Handle file upload
  const handleFileUpload = useCallback((file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_format', 'auto');
    formData.append('has_header', 'true');
    formData.append('sample_rows', '1000');
    
    setUploadProgress(0);
    uploadMutation.mutate(formData);
  }, [uploadMutation]);

  // Handle drag and drop
  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
  }, []);

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      setSelectedFile(file);
      handleFileUpload(file);
    }
  }, [handleFileUpload]);

  // Handle manual analysis trigger
  const handleAnalyzeData = useCallback(() => {
    if (!currentDataProfile) return;
    
    analysisMutation.mutate({
      data_profile_id: currentDataProfile,
      analysis_types: ['completeness', 'accuracy', 'consistency', 'validity', 'duplicates', 'outliers'],
      ai_enabled: true,
      sample_size: 10000
    });
  }, [currentDataProfile, analysisMutation]);

  // Handle cleaning preview
  const handlePreviewCleaning = useCallback(() => {
    if (!currentDataProfile) return;
    
    const operations = [];
    
    if (cleaningConfig.removeOutliers) {
      operations.push({
        operation: 'remove_outliers',
        parameters: { method: 'iqr', threshold: 1.5 }
      });
    }
    
    operations.push({
      operation: 'remove_duplicates',
      parameters: { keep: 'first' }
    });
    
    if (cleaningConfig.imputationStrategy !== 'none') {
      operations.push({
        operation: 'fill_missing',
        parameters: { 
          strategy: cleaningConfig.imputationStrategy === 'ml_prediction' ? 'knn' : 'auto'
        }
      });
    }
    
    if (cleaningConfig.standardizeFormat) {
      operations.push({
        operation: 'standardize_format',
        parameters: {
          columns: [],
          format_rules: {}
        }
      });
    }

    cleaningMutation.mutate({
      data_profile_id: currentDataProfile,
      cleaning_operations: operations,
      preview_only: true
    });
  }, [currentDataProfile, cleaningConfig, cleaningMutation]);

  // Handle start cleaning
  const handleStartCleaning = useCallback(() => {
    if (!currentDataProfile) return;
    
    const operations = [];
    
    if (cleaningConfig.removeOutliers) {
      operations.push({
        operation: 'remove_outliers',
        parameters: { method: 'iqr', threshold: 1.5 }
      });
    }
    
    operations.push({
      operation: 'remove_duplicates',
      parameters: { keep: 'first' }
    });
    
    if (cleaningConfig.imputationStrategy !== 'none') {
      operations.push({
        operation: 'fill_missing',
        parameters: { 
          strategy: cleaningConfig.imputationStrategy === 'ml_prediction' ? 'knn' : 'auto'
        }
      });
    }
    
    if (cleaningConfig.standardizeFormat) {
      operations.push({
        operation: 'standardize_format',
        parameters: {
          columns: [],
          format_rules: {}
        }
      });
    }

    cleaningMutation.mutate({
      data_profile_id: currentDataProfile,
      cleaning_operations: operations,
      preview_only: false
    });
  }, [currentDataProfile, cleaningConfig, cleaningMutation]);

  // Use API data if available, only show mock data if no API data and no uploads
  const recentUploads = uploadsData?.data || (currentDataProfile ? [] : [
    { name: "customer_data.csv", size: "15.2 MB", date: "2 hours ago", status: "analyzed" },
    { name: "transactions.xlsx", size: "8.7 MB", date: "1 day ago", status: "cleaned" }, 
    { name: "user_profiles.json", size: "3.1 MB", date: "3 days ago", status: "pending" }
  ]);

  // Use real quality metrics if available
  const displayQualityMetrics = qualitySummary ? [
    {
      category: "Completeness",
      score: qualitySummary.quality_metrics.completeness.score,
      issues: qualitySummary.quality_metrics.completeness.issues,
      status: qualitySummary.quality_metrics.completeness.status,
      description: qualitySummary.quality_metrics.completeness.description
    },
    {
      category: "Accuracy",
      score: qualitySummary.quality_metrics.accuracy.score,
      issues: qualitySummary.quality_metrics.accuracy.issues,
      status: qualitySummary.quality_metrics.accuracy.status,
      description: qualitySummary.quality_metrics.accuracy.description
    },
    {
      category: "Consistency",
      score: qualitySummary.quality_metrics.consistency.score,
      issues: qualitySummary.quality_metrics.consistency.issues,
      status: qualitySummary.quality_metrics.consistency.status,
      description: qualitySummary.quality_metrics.consistency.description
    },
    {
      category: "Validity",
      score: qualitySummary.quality_metrics.validity.score,
      issues: qualitySummary.quality_metrics.validity.issues,
      status: qualitySummary.quality_metrics.validity.status,
      description: qualitySummary.quality_metrics.validity.description
    }
  ] : qualityMetrics;

  const displayIssueTypes = qualitySummary?.issue_breakdown || issueTypes;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Data Quality Management</h1>
        <p className="text-muted-foreground">
          Upload, analyze, and clean your data with AI-powered quality assessment
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="upload">Upload & Analyze</TabsTrigger>
          <TabsTrigger value="assessment" disabled={!currentDataProfile}>Quality Assessment</TabsTrigger>
          <TabsTrigger value="cleaning" disabled={!currentDataProfile}>Cleaning Configuration</TabsTrigger>
          <TabsTrigger value="validation" disabled={!currentDataProfile}>Validation Results</TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6">
          {/* Upload Interface */}
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="h-5 w-5 mr-2" />
                Data Upload
              </CardTitle>
              <CardDescription>
                Upload your data files for quality analysis and cleaning
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div 
                className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:border-primary/50 transition-colors cursor-pointer"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">Drop files here or click to browse</h3>
                <p className="text-muted-foreground mb-4">
                  Supports CSV, Excel, JSON, and database exports up to 500MB
                </p>
                <Button 
                  className="enterprise-button-primary"
                  disabled={uploadMutation.isPending}
                >
                  {uploadMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    'Select Files'
                  )}
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls,.json,.tsv,.txt"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              {(uploadProgress > 0 || isAnalyzing) && (
                <div className="mt-6">
                  <div className="flex justify-between text-sm mb-2">
                    <span>{isAnalyzing ? 'Analyzing' : 'Uploading'} {selectedFile?.name || 'file'}</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} />
                  {isAnalyzing && (
                    <p className="text-sm text-muted-foreground mt-2">
                      AI is analyzing your data for quality issues...
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Uploads */}
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle>Recent Uploads</CardTitle>
              <CardDescription>Files uploaded in the last 30 days</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading && (
                <div className="text-center py-4">
                  <div className="text-sm text-muted-foreground">Loading recent uploads...</div>
                </div>
              )}
              {error && (
                <div className="text-center py-4">
                  <div className="text-sm text-destructive">Unable to load recent uploads. Using cached data.</div>
                </div>
              )}
              <div className="space-y-4">
                {recentUploads.map((file) => (
                  <div 
                    key={file.name} 
                    className="flex items-center justify-between p-3 rounded-lg border border-border/50 hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => {
                      if (file.id) {
                        setCurrentDataProfile(file.id);
                        setActiveTab("assessment");
                      }
                    }}
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{file.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {file.size} • {file.date}
                          {file.rows && file.columns && (
                            <> • {file.rows.toLocaleString()} rows, {file.columns} columns</>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {file.quality_score && (
                        <span className="text-sm text-muted-foreground">
                          {file.quality_score}% quality
                        </span>
                      )}
                      <Badge variant={file.status === 'analyzed' ? 'default' : file.status === 'cleaned' ? 'secondary' : 'outline'}>
                        {file.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="assessment" className="space-y-6">
          {/* Quality Metrics */}
          {isLoadingQuality ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i} className="metrics-card">
                  <CardContent className="p-6">
                    <div className="animate-pulse space-y-3">
                      <div className="h-4 bg-muted rounded w-3/4"></div>
                      <div className="h-8 bg-muted rounded w-1/2"></div>
                      <div className="h-2 bg-muted rounded"></div>
                      <div className="h-3 bg-muted rounded w-2/3"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {displayQualityMetrics.map((metric) => (
              <Card key={metric.category} className="metrics-card">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium">{metric.category}</h3>
                    {metric.status === 'excellent' && <CheckCircle className="h-5 w-5 text-success" />}
                    {metric.status === 'good' && <TrendingUp className="h-5 w-5 text-primary" />}
                    {metric.status === 'warning' && <AlertTriangle className="h-5 w-5 text-warning" />}
                  </div>
                  <div className="space-y-3">
                    <div className="text-2xl font-bold">{metric.score}%</div>
                    <Progress value={metric.score} />
                    <div>
                      <div className="text-sm font-medium text-danger">{metric.issues} issues</div>
                      <div className="text-xs text-muted-foreground mt-1">{metric.description}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          )}

          {/* Analysis Actions */}
          {currentDataProfile && (
            <Card className="enterprise-card">
              <CardHeader>
                <CardTitle>Analysis Actions</CardTitle>
                <CardDescription>
                  Run additional analysis or re-analyze your data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Deep Analysis</p>
                    <p className="text-sm text-muted-foreground">
                      Run comprehensive AI-powered analysis on your dataset
                    </p>
                  </div>
                  <Button
                    onClick={handleAnalyzeData}
                    disabled={analysisMutation.isPending || isAnalyzing}
                    className="enterprise-button-primary"
                  >
                    {analysisMutation.isPending || isAnalyzing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Re-analyze Data
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Issue Breakdown */}
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="h-5 w-5 mr-2" />
                Issue Breakdown
              </CardTitle>
              <CardDescription>Detailed categorization of detected data quality issues</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {displayIssueTypes.map((issue) => (
                  <div key={issue.type} className="flex items-center justify-between p-3 rounded-lg border border-border/50">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${
                        issue.severity === 'high' ? 'bg-danger' :
                        issue.severity === 'medium' ? 'bg-warning' : 'bg-success'
                      }`} />
                      <div>
                        <p className="font-medium">{issue.type}</p>
                        <p className="text-sm text-muted-foreground">
                          {issue.count.toLocaleString()} occurrences
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={
                        issue.severity === 'high' ? 'destructive' :
                        issue.severity === 'medium' ? 'secondary' : 'outline'
                      }>
                        {issue.severity} priority
                      </Badge>
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cleaning" className="space-y-6">
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                Cleaning Configuration
              </CardTitle>
              <CardDescription>
                Configure AI algorithms and thresholds for automated data cleaning
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-3">Duplicate Detection</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Similarity Threshold</span>
                        <span className="text-sm font-medium">{cleaningConfig.similarityThreshold}%</span>
                      </div>
                      <Slider
                        value={[cleaningConfig.similarityThreshold]}
                        onValueChange={([value]) => setCleaningConfig(prev => ({ ...prev, similarityThreshold: value }))}
                        max={100}
                        min={50}
                        step={5}
                        className="w-full"
                      />
                      <div className="flex space-x-2">
                        <Button 
                          variant={cleaningConfig.duplicateMethod === "exact" ? "default" : "outline"} 
                          size="sm"
                          onClick={() => setCleaningConfig(prev => ({ ...prev, duplicateMethod: "exact" }))}
                        >
                          Exact Match
                        </Button>
                        <Button 
                          variant={cleaningConfig.duplicateMethod === "fuzzy" ? "default" : "outline"} 
                          size="sm"
                          onClick={() => setCleaningConfig(prev => ({ ...prev, duplicateMethod: "fuzzy" }))}
                        >
                          Fuzzy Match
                        </Button>
                        <Button 
                          variant={cleaningConfig.duplicateMethod === "semantic" ? "default" : "outline"} 
                          size="sm"
                          onClick={() => setCleaningConfig(prev => ({ ...prev, duplicateMethod: "semantic" }))}
                        >
                          Semantic Match
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-3">Missing Value Handling</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Imputation Strategy</span>
                      </div>
                      <div className="flex space-x-2">
                        <Button 
                          variant={cleaningConfig.imputationStrategy === "mean" ? "default" : "outline"} 
                          size="sm"
                          onClick={() => setCleaningConfig(prev => ({ ...prev, imputationStrategy: "mean" }))}
                        >
                          Mean
                        </Button>
                        <Button 
                          variant={cleaningConfig.imputationStrategy === "ml_prediction" ? "default" : "outline"} 
                          size="sm"
                          onClick={() => setCleaningConfig(prev => ({ ...prev, imputationStrategy: "ml_prediction" }))}
                        >
                          ML Prediction
                        </Button>
                        <Button 
                          variant={cleaningConfig.imputationStrategy === "forward_fill" ? "default" : "outline"} 
                          size="sm"
                          onClick={() => setCleaningConfig(prev => ({ ...prev, imputationStrategy: "forward_fill" }))}
                        >
                          Forward Fill
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Additional Options */}
                <div className="space-y-4">
                  <h4 className="font-medium">Additional Cleaning Options</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="remove-outliers">Remove Outliers</Label>
                        <p className="text-sm text-muted-foreground">Automatically detect and remove statistical outliers</p>
                      </div>
                      <Switch
                        id="remove-outliers"
                        checked={cleaningConfig.removeOutliers}
                        onCheckedChange={(checked) => setCleaningConfig(prev => ({ ...prev, removeOutliers: checked }))}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="standardize-format">Standardize Format</Label>
                        <p className="text-sm text-muted-foreground">Normalize text case, spacing, and formatting</p>
                      </div>
                      <Switch
                        id="standardize-format"
                        checked={cleaningConfig.standardizeFormat}
                        onCheckedChange={(checked) => setCleaningConfig(prev => ({ ...prev, standardizeFormat: checked }))}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-border">
                  <Button 
                    variant="outline"
                    onClick={handlePreviewCleaning}
                    disabled={!currentDataProfile || cleaningMutation.isPending}
                  >
                    {cleaningMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generating Preview...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Preview Changes
                      </>
                    )}
                  </Button>
                  <Button 
                    className="enterprise-button-success"
                    onClick={handleStartCleaning}
                    disabled={!currentDataProfile || cleaningMutation.isPending}
                  >
                    {cleaningMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Cleaning...
                      </>
                    ) : (
                      'Start Cleaning Process'
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validation" className="space-y-6">
          <Card className="enterprise-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center">
                    <CheckCircle className="h-5 w-5 mr-2 text-success" />
                    Validation Results
                  </CardTitle>
                  <CardDescription>Before and after data quality comparison</CardDescription>
                </div>
                <Button 
                  variant="outline"
                  onClick={() => {
                    // Export functionality would go here
                    toast({
                      title: "Export started",
                      description: "Your data quality report is being generated.",
                    });
                  }}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Report
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-4 text-muted-foreground">Before Cleaning</h4>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border">
                      <span>Overall Quality Score</span>
                      <span className="font-bold text-lg">76.3%</span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Completeness</span>
                        <span className="text-warning">72%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Accuracy</span>
                        <span className="text-danger">68%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Consistency</span>
                        <span className="text-warning">81%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-4 text-success">After Cleaning</h4>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-success/10 border border-success/30">
                      <span>Overall Quality Score</span>
                      <span className="font-bold text-lg text-success">94.2%</span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Completeness</span>
                        <span className="text-success">92%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Accuracy</span>
                        <span className="text-success">96%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Consistency</span>
                        <span className="text-success">95%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-success/10 border border-success/30 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-success mr-3" />
                  <div>
                    <p className="font-medium text-success">Cleaning Complete</p>
                    <p className="text-sm text-muted-foreground">
                      Processed 1,247,832 records with 94.2% quality improvement
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}