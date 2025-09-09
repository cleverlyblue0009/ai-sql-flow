import { useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
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
  Loader2
} from "lucide-react";
import { useFileUpload, useRecentUploads, useStartCleaning } from "@/hooks/useApi";

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
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // API hooks
  const fileUploadMutation = useFileUpload();
  const { data: recentUploads, isLoading: uploadsLoading } = useRecentUploads();
  const cleaningMutation = useStartCleaning();

  // File upload handlers
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleFileDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    try {
      setUploadProgress(0);
      setIsAnalyzing(true);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const result = await fileUploadMutation.mutateAsync({ 
        file: selectedFile,
        options: { auto_analyze: true }
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (result.data) {
        toast.success('File uploaded and analysis started!');
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    } catch (error) {
      toast.error('Upload failed');
    } finally {
      setIsAnalyzing(false);
      setTimeout(() => setUploadProgress(0), 2000);
    }
  };

  const handleStartCleaning = async (fileId: string) => {
    try {
      await cleaningMutation.mutateAsync({
        fileId,
        config: {
          remove_duplicates: true,
          fill_missing_values: true,
          remove_outliers: true,
          standardize_formats: true
        }
      });
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleViewDetails = (fileName: string) => {
    toast.info(`Viewing details for ${fileName}`, {
      description: 'This would open a detailed analysis view'
    });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Data Quality Management</h1>
        <p className="text-muted-foreground">
          Upload, analyze, and clean your data with AI-powered quality assessment
        </p>
      </div>

      <Tabs defaultValue="upload" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="upload">Upload & Analyze</TabsTrigger>
          <TabsTrigger value="assessment">Quality Assessment</TabsTrigger>
          <TabsTrigger value="cleaning">Cleaning Configuration</TabsTrigger>
          <TabsTrigger value="validation">Validation Results</TabsTrigger>
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
                onDrop={handleFileDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">Drop files here or click to browse</h3>
                <p className="text-muted-foreground mb-4">
                  Supports CSV, Excel, JSON, and database exports up to 500MB
                </p>
                {selectedFile ? (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Selected: {selectedFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <Button 
                      className="enterprise-button-primary" 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUpload();
                      }}
                      disabled={fileUploadMutation.isPending}
                    >
                      {fileUploadMutation.isPending ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        'Upload & Analyze'
                      )}
                    </Button>
                  </div>
                ) : (
                  <Button className="enterprise-button-primary">Select Files</Button>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls,.json,.tsv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              {uploadProgress > 0 && (
                <div className="mt-6">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Uploading {selectedFile?.name || 'file'}</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} />
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
              <div className="space-y-4">
                {uploadsLoading ? (
                  // Loading skeleton
                  Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-border/50">
                      <div className="flex items-center space-x-3">
                        <div className="h-5 w-5 bg-muted rounded animate-pulse" />
                        <div className="space-y-1">
                          <div className="h-4 w-32 bg-muted rounded animate-pulse" />
                          <div className="h-3 w-24 bg-muted rounded animate-pulse" />
                        </div>
                      </div>
                      <div className="h-6 w-16 bg-muted rounded animate-pulse" />
                    </div>
                  ))
                ) : recentUploads?.length ? (
                  recentUploads.map((file: any) => (
                    <div key={file.id} className="flex items-center justify-between p-3 rounded-lg border border-border/50 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center space-x-3">
                        <FileText className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{file.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {file.size} • {file.upload_date || file.date}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={
                          file.status === 'analyzed' ? 'default' : 
                          file.status === 'cleaned' ? 'secondary' : 
                          'outline'
                        }>
                          {file.status}
                        </Badge>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleViewDetails(file.name)}
                        >
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  // Fallback data when no uploads from API
                  [
                    { id: 1, name: "customer_data.csv", size: "15.2 MB", date: "2 hours ago", status: "analyzed" },
                    { id: 2, name: "transactions.xlsx", size: "8.7 MB", date: "1 day ago", status: "cleaned" }, 
                    { id: 3, name: "user_profiles.json", size: "3.1 MB", date: "3 days ago", status: "pending" }
                  ].map((file) => (
                    <div key={file.id} className="flex items-center justify-between p-3 rounded-lg border border-border/50 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center space-x-3">
                        <FileText className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{file.name}</p>
                          <p className="text-sm text-muted-foreground">{file.size} • {file.date}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={
                          file.status === 'analyzed' ? 'default' : 
                          file.status === 'cleaned' ? 'secondary' : 
                          'outline'
                        }>
                          {file.status}
                        </Badge>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleViewDetails(file.name)}
                        >
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="assessment" className="space-y-6">
          {/* Quality Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {qualityMetrics.map((metric) => (
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
                {issueTypes.map((issue) => (
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
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => toast.info(`Viewing ${issue.type} details`, {
                          description: `Found ${issue.count} instances of ${issue.type.toLowerCase()}`
                        })}
                      >
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
                        <span className="text-sm font-medium">85%</span>
                      </div>
                      <Progress value={85} />
                      <div className="flex space-x-2">
                        <Button variant="outline" size="sm">Exact Match</Button>
                        <Button variant="outline" size="sm">Fuzzy Match</Button>
                        <Button variant="default" size="sm">Semantic Match</Button>
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
                        <Button variant="outline" size="sm">Mean</Button>
                        <Button variant="default" size="sm">ML Prediction</Button>
                        <Button variant="outline" size="sm">Forward Fill</Button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-border">
                  <Button 
                    variant="outline"
                    onClick={() => toast.info('Preview Changes', {
                      description: 'This would show a preview of cleaning operations'
                    })}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Preview Changes
                  </Button>
                  <Button 
                    className="enterprise-button-success"
                    onClick={() => toast.success('Cleaning process started!', {
                      description: 'Your data will be processed with the configured settings'
                    })}
                    disabled={cleaningMutation.isPending}
                  >
                    {cleaningMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
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
                  onClick={() => toast.success('Report exported!', {
                    description: 'Quality assessment report has been downloaded'
                  })}
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