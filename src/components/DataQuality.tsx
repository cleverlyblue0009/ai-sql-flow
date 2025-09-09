import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  BarChart3
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
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

  // Fetch recent uploads from API
  const { data: uploadsData, isLoading, error } = useQuery({
    queryKey: ['recent-uploads'],
    queryFn: api.dataQuality.getRecentUploads,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Use API data if available, otherwise fall back to static data
  const recentUploads = uploadsData?.data || [
    { name: "customer_data.csv", size: "15.2 MB", date: "2 hours ago", status: "analyzed" },
    { name: "transactions.xlsx", size: "8.7 MB", date: "1 day ago", status: "cleaned" }, 
    { name: "user_profiles.json", size: "3.1 MB", date: "3 days ago", status: "pending" }
  ];

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
              <div className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:border-primary/50 transition-colors cursor-pointer">
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">Drop files here or click to browse</h3>
                <p className="text-muted-foreground mb-4">
                  Supports CSV, Excel, JSON, and database exports up to 500MB
                </p>
                <Button className="enterprise-button-primary">Select Files</Button>
              </div>

              {uploadProgress > 0 && (
                <div className="mt-6">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Uploading customer_data.csv</span>
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
                  <div key={file.name} className="flex items-center justify-between p-3 rounded-lg border border-border/50">
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{file.name}</p>
                        <p className="text-sm text-muted-foreground">{file.size} • {file.date}</p>
                      </div>
                    </div>
                    <Badge variant={file.status === 'analyzed' ? 'default' : file.status === 'cleaned' ? 'secondary' : 'outline'}>
                      {file.status}
                    </Badge>
                  </div>
                ))}
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
                  <Button variant="outline">
                    <Play className="h-4 w-4 mr-2" />
                    Preview Changes
                  </Button>
                  <Button className="enterprise-button-success">
                    Start Cleaning Process
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
                <Button variant="outline">
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