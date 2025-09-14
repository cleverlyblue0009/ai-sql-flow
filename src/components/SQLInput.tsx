import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Editor } from '@monaco-editor/react';
import { format } from 'sql-formatter';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Upload, 
  FileText, 
  Code, 
  Database, 
  CheckCircle, 
  AlertTriangle, 
  Eye,
  Download,
  RefreshCw,
  Zap
} from 'lucide-react';

interface SQLInputProps {
  onSQLChange: (sql: string, metadata?: any) => void;
  onAnalysisComplete: (analysis: any) => void;
  selectedDatabase?: string;
}

interface SQLAnalysis {
  tables: string[];
  schemas: string[];
  operations: string[];
  complexity: 'low' | 'medium' | 'high';
  warnings: string[];
  lineCount: number;
  estimatedMigrationTime: string;
}

interface FileUploadStatus {
  uploading: boolean;
  progress: number;
  error?: string;
  success?: boolean;
}

const SQLInput: React.FC<SQLInputProps> = ({ 
  onSQLChange, 
  onAnalysisComplete, 
  selectedDatabase = 'mysql' 
}) => {
  const [sqlContent, setSQLContent] = useState('');
  const [activeTab, setActiveTab] = useState('editor');
  const [analysis, setAnalysis] = useState<SQLAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<FileUploadStatus>({
    uploading: false,
    progress: 0
  });
  const editorRef = useRef(null);

  // File upload handler
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (!file.name.match(/\.(sql|txt)$/i)) {
      setUploadStatus({
        uploading: false,
        progress: 0,
        error: 'Please upload a .sql or .txt file'
      });
      return;
    }

    setUploadStatus({ uploading: true, progress: 0 });

    try {
      const text = await file.text();
      
      // Simulate upload progress
      for (let i = 0; i <= 100; i += 10) {
        setUploadStatus(prev => ({ ...prev, progress: i }));
        await new Promise(resolve => setTimeout(resolve, 50));
      }

      setSQLContent(text);
      onSQLChange(text, { fileName: file.name, fileSize: file.size });
      
      setUploadStatus({ 
        uploading: false, 
        progress: 100, 
        success: true 
      });
      
      // Auto-analyze after upload
      await analyzeSQLContent(text);
      
      // Switch to editor tab to show the content
      setActiveTab('editor');

    } catch (error) {
      setUploadStatus({
        uploading: false,
        progress: 0,
        error: 'Failed to read file content'
      });
    }
  }, [onSQLChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.sql', '.txt'],
      'application/sql': ['.sql']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024 // 10MB limit
  });

  // SQL Analysis function
  const analyzeSQLContent = async (content: string) => {
    if (!content.trim()) return;

    setIsAnalyzing(true);
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Basic SQL analysis
      const lines = content.split('\n').filter(line => line.trim());
      const upperContent = content.toUpperCase();
      
      // Extract tables (basic pattern matching)
      const tableMatches = content.match(/(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)/gi) || [];
      const tables = [...new Set(tableMatches.map(match => 
        match.replace(/^(FROM|JOIN|INTO|UPDATE)\s+/i, '').trim()
      ))];

      // Extract schemas
      const schemaMatches = content.match(/([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)/g) || [];
      const schemas = [...new Set(schemaMatches.map(match => match.split('.')[0]))];

      // Detect operations
      const operations = [];
      if (upperContent.includes('SELECT')) operations.push('SELECT');
      if (upperContent.includes('INSERT')) operations.push('INSERT');
      if (upperContent.includes('UPDATE')) operations.push('UPDATE');
      if (upperContent.includes('DELETE')) operations.push('DELETE');
      if (upperContent.includes('CREATE')) operations.push('CREATE');
      if (upperContent.includes('ALTER')) operations.push('ALTER');
      if (upperContent.includes('DROP')) operations.push('DROP');

      // Determine complexity
      let complexity: 'low' | 'medium' | 'high' = 'low';
      const complexityScore = 
        (content.match(/JOIN/gi) || []).length * 2 +
        (content.match(/SUBQUERY|EXISTS|CASE/gi) || []).length * 3 +
        (content.match(/UNION|INTERSECT|EXCEPT/gi) || []).length * 2 +
        tables.length;

      if (complexityScore > 15) complexity = 'high';
      else if (complexityScore > 5) complexity = 'medium';

      // Generate warnings
      const warnings = [];
      if (content.includes('SELECT *')) {
        warnings.push('Consider specifying column names instead of SELECT *');
      }
      if (content.match(/WHERE.*=.*NULL/i)) {
        warnings.push('Use IS NULL instead of = NULL for null comparisons');
      }
      if (tables.length > 10) {
        warnings.push('High number of tables detected - consider breaking into smaller queries');
      }

      // Estimate migration time
      let estimatedTime = '2-5 minutes';
      if (complexity === 'high' || lines.length > 500) {
        estimatedTime = '10-30 minutes';
      } else if (complexity === 'medium' || lines.length > 100) {
        estimatedTime = '5-15 minutes';
      }

      const analysisResult: SQLAnalysis = {
        tables,
        schemas,
        operations,
        complexity,
        warnings,
        lineCount: lines.length,
        estimatedMigrationTime: estimatedTime
      };

      setAnalysis(analysisResult);
      onAnalysisComplete(analysisResult);

    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle editor change
  const handleEditorChange = (value: string | undefined) => {
    const content = value || '';
    setSQLContent(content);
    onSQLChange(content);
  };

  // Format SQL
  const formatSQL = () => {
    if (!sqlContent.trim()) return;
    
    try {
      const formatted = format(sqlContent, {
        language: selectedDatabase === 'postgresql' ? 'postgresql' : 'mysql',
        keywordCase: 'upper',
        identifierCase: 'lower',
        indentStyle: 'standard'
      });
      setSQLContent(formatted);
      onSQLChange(formatted);
    } catch (error) {
      console.error('Failed to format SQL:', error);
    }
  };

  // Clear editor
  const clearEditor = () => {
    setSQLContent('');
    setAnalysis(null);
    setUploadStatus({ uploading: false, progress: 0 });
    onSQLChange('');
  };

  return (
    <Card className="enterprise-card">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Code className="h-5 w-5 mr-2" />
          SQL Input & Analysis
        </CardTitle>
        <CardDescription>
          Upload SQL files or write SQL directly with real-time analysis and validation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload">File Upload</TabsTrigger>
            <TabsTrigger value="editor">SQL Editor</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive 
                  ? 'border-primary bg-primary/5' 
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              
              {uploadStatus.uploading ? (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Uploading...</p>
                  <Progress value={uploadStatus.progress} className="w-full max-w-xs mx-auto" />
                  <p className="text-xs text-muted-foreground">{uploadStatus.progress}%</p>
                </div>
              ) : (
                <div>
                  <p className="text-lg font-medium mb-2">
                    {isDragActive ? 'Drop your SQL file here' : 'Drag & drop SQL files here'}
                  </p>
                  <p className="text-sm text-muted-foreground mb-4">
                    or click to browse files (.sql, .txt up to 10MB)
                  </p>
                  <Button variant="outline">
                    <FileText className="h-4 w-4 mr-2" />
                    Browse Files
                  </Button>
                </div>
              )}
            </div>

            {uploadStatus.error && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{uploadStatus.error}</AlertDescription>
              </Alert>
            )}

            {uploadStatus.success && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>File uploaded and analyzed successfully!</AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="editor" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Badge variant="outline">
                  <Database className="h-3 w-3 mr-1" />
                  {selectedDatabase.toUpperCase()}
                </Badge>
                {sqlContent && (
                  <Badge variant="secondary">
                    {sqlContent.split('\n').filter(line => line.trim()).length} lines
                  </Badge>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" onClick={formatSQL} disabled={!sqlContent}>
                  <Zap className="h-4 w-4 mr-1" />
                  Format
                </Button>
                <Button variant="outline" size="sm" onClick={() => analyzeSQLContent(sqlContent)} disabled={!sqlContent || isAnalyzing}>
                  <RefreshCw className={`h-4 w-4 mr-1 ${isAnalyzing ? 'animate-spin' : ''}`} />
                  Analyze
                </Button>
                <Button variant="outline" size="sm" onClick={clearEditor}>
                  Clear
                </Button>
              </div>
            </div>

            <div className="border rounded-lg overflow-hidden">
              <Editor
                height="400px"
                defaultLanguage="sql"
                value={sqlContent}
                onChange={handleEditorChange}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  lineNumbers: 'on',
                  wordWrap: 'on',
                  automaticLayout: true,
                  tabSize: 2,
                  insertSpaces: true,
                  formatOnPaste: true,
                  formatOnType: true
                }}
                onMount={(editor) => {
                  editorRef.current = editor;
                }}
              />
            </div>

            {sqlContent && (
              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <span>Characters: {sqlContent.length}</span>
                  <span>Lines: {sqlContent.split('\n').length}</span>
                  <span>Words: {sqlContent.split(/\s+/).filter(word => word.length > 0).length}</span>
                </div>
                <Button variant="ghost" size="sm">
                  <Download className="h-4 w-4 mr-1" />
                  Export SQL
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="analysis" className="space-y-4">
            {isAnalyzing ? (
              <div className="flex items-center justify-center p-8">
                <RefreshCw className="h-8 w-8 animate-spin mr-3" />
                <div>
                  <p className="font-medium">Analyzing SQL...</p>
                  <p className="text-sm text-muted-foreground">
                    Extracting schema information and detecting patterns
                  </p>
                </div>
              </div>
            ) : analysis ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Overview */}
                <Card className="border border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center">
                      <Eye className="h-5 w-5 mr-2" />
                      Overview
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Complexity</span>
                      <Badge variant={
                        analysis.complexity === 'high' ? 'destructive' :
                        analysis.complexity === 'medium' ? 'default' : 'secondary'
                      }>
                        {analysis.complexity.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Lines of Code</span>
                      <span className="font-medium">{analysis.lineCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Estimated Migration</span>
                      <span className="font-medium">{analysis.estimatedMigrationTime}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Database Objects */}
                <Card className="border border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center">
                      <Database className="h-5 w-5 mr-2" />
                      Database Objects
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-muted-foreground">Tables</span>
                        <span className="font-medium">{analysis.tables.length}</span>
                      </div>
                      {analysis.tables.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {analysis.tables.slice(0, 3).map(table => (
                            <Badge key={table} variant="outline" className="text-xs">
                              {table}
                            </Badge>
                          ))}
                          {analysis.tables.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{analysis.tables.length - 3} more
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-muted-foreground">Operations</span>
                        <span className="font-medium">{analysis.operations.length}</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {analysis.operations.map(op => (
                          <Badge key={op} variant="secondary" className="text-xs">
                            {op}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Warnings */}
                {analysis.warnings.length > 0 && (
                  <Card className="border border-border/50 md:col-span-2">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg flex items-center text-warning">
                        <AlertTriangle className="h-5 w-5 mr-2" />
                        Warnings & Recommendations
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {analysis.warnings.map((warning, index) => (
                          <Alert key={index}>
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>{warning}</AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <div className="text-center p-8 text-muted-foreground">
                <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="font-medium mb-2">No Analysis Available</p>
                <p className="text-sm">
                  Upload a SQL file or write SQL code to see detailed analysis
                </p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default SQLInput;