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
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
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
  Zap,
  X,
  Plus,
  Folder,
  ArrowRight,
  Clock,
  AlertCircle,
  FileCode,
  Package,
  Trash2
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

export interface SQLFile {
  id: string;
  name: string;
  content: string;
  size: number;
  detectedDialect: string;
  confidence: number;
  analysis: SQLAnalysis | null;
  status: 'uploading' | 'analyzing' | 'ready' | 'error' | 'translating' | 'translated';
  error?: string;
  dependencies: string[];
  translatedContent?: string;
  uploadProgress: number;
}

export interface SQLAnalysis {
  tables: string[];
  views: string[];
  procedures: string[];
  functions: string[];
  schemas: string[];
  operations: string[];
  complexity: 'low' | 'medium' | 'high';
  warnings: string[];
  errors: string[];
  lineCount: number;
  estimatedMigrationTime: string;
  dialectFeatures: string[];
  unsupportedFeatures: string[];
}

export interface DialectDetectionResult {
  dialect: string;
  confidence: number;
  features: string[];
  patterns: string[];
}

interface MultiFileSQLInputProps {
  onFilesChange: (files: SQLFile[]) => void;
  onAnalysisComplete: (analysis: any) => void;
  targetDialect?: string;
}

// Dialect detection patterns - Enhanced for better detection
const DIALECT_PATTERNS = {
  mysql: {
    keywords: ['AUTO_INCREMENT', 'ENGINE=InnoDB', 'ENGINE=MyISAM', 'CHARSET=utf8mb4', 'DELIMITER //', 'TINYINT', 'MEDIUMINT', 'LONGTEXT', 'ENUM(', 'SET(', 'ZEROFILL', 'AFTER ', 'FIRST ', 'MODIFY COLUMN'],
    functions: ['CURDATE()', 'DATE_SUB(', 'JSON_EXTRACT(', 'IFNULL(', 'DATE_FORMAT(', 'CONCAT_WS(', 'GROUP_CONCAT(', 'UNIX_TIMESTAMP('],
    operators: ['`', 'LIMIT ', 'UNSIGNED', 'COLLATE utf8'],
    datatypes: ['TINYINT', 'MEDIUMINT', 'BIGINT', 'LONGTEXT', 'MEDIUMTEXT', 'TINYTEXT', 'DOUBLE'],
    weight: 1.0
  },
  postgresql: {
    keywords: ['SERIAL', 'BIGSERIAL', 'GENERATE_ALWAYS AS IDENTITY', 'RETURNING', 'ARRAY[', 'JSONB', 'UUID', 'SMALLSERIAL', 'GENERATE_ALWAYS', 'ON CONFLICT'],
    functions: ['NOW()', 'CURRENT_DATE', 'AGE(', 'COALESCE(', 'EXTRACT(', 'STRING_AGG(', 'ARRAY_AGG(', 'GENERATE_SERIES('],
    operators: ['::', '||', 'ILIKE', 'SIMILAR TO', '~', '!~', 'ANY(', 'ALL('],
    datatypes: ['SERIAL', 'BIGSERIAL', 'SMALLSERIAL', 'BYTEA', 'TEXT', 'BOOLEAN', 'INET', 'JSON', 'JSONB'],
    weight: 1.0
  },
  mssql: {
    keywords: ['IDENTITY(1,1)', 'TOP ', 'GO', 'NVARCHAR', 'UNIQUEIDENTIFIER', 'BIT', 'WITH (NOLOCK)', 'OUTPUT ', 'INSERTED', 'DELETED'],
    functions: ['GETDATE()', 'DATEPART(', 'ISNULL(', 'LEN(', 'CHARINDEX(', 'STUFF(', 'CAST(', 'CONVERT('],
    operators: ['[', ']', 'WITH (NOLOCK)', 'MERGE ', 'OUTPUT'],
    datatypes: ['NVARCHAR', 'NCHAR', 'NTEXT', 'UNIQUEIDENTIFIER', 'DATETIME2', 'DATETIMEOFFSET', 'HIERARCHYID'],
    weight: 1.0
  },
  oracle: {
    keywords: ['SEQUENCE', 'DUAL', 'ROWNUM', 'VARCHAR2', 'NUMBER', 'CLOB', 'BLOB', 'NVARCHAR2', 'ROWID', 'TRIGGER'],
    functions: ['SYSDATE', 'SUBSTR(', 'NVL(', 'DECODE(', 'TO_CHAR(', 'TO_DATE(', 'TO_NUMBER(', 'TRUNC('],
    operators: ['BEGIN', 'END;', 'EXCEPTION', 'WHEN', '||', 'CONNECT BY', 'START WITH'],
    datatypes: ['VARCHAR2', 'NVARCHAR2', 'NUMBER', 'CLOB', 'NCLOB', 'BLOB', 'BFILE', 'ROWID'],
    weight: 1.0
  },
  snowflake: {
    keywords: ['AUTOINCREMENT', 'VARIANT', 'QUALIFY', 'DISTKEY', 'SORTKEY', 'CLUSTER BY', 'COPY INTO', 'WAREHOUSE'],
    functions: ['CURRENT_TIMESTAMP()', 'DATEDIFF(', 'DATEADD(', 'TRY_PARSE_JSON(', 'PARSE_JSON(', 'TRY_CAST(', 'FLATTEN('],
    operators: ['"', 'SAMPLE(', 'FLATTEN(', 'QUALIFY ', '::', 'MATCH_RECOGNIZE'],
    datatypes: ['VARIANT', 'OBJECT', 'ARRAY', 'GEOGRAPHY', 'TIMESTAMP_TZ', 'TIMESTAMP_LTZ', 'TIMESTAMP_NTZ'],
    weight: 1.0
  },
  redshift: {
    keywords: ['DISTKEY', 'SORTKEY', 'DISTSTYLE', 'ENCODE', 'VACUUM', 'ANALYZE', 'COMPOUND SORTKEY', 'INTERLEAVED SORTKEY'],
    functions: ['DATEADD(', 'DATEDIFF(', 'GETDATE(', 'NVL(', 'NVL2(', 'LISTAGG(', 'MEDIAN('],
    operators: ['COPY', 'UNLOAD', 'DISTKEY', 'SORTKEY', 'DISTSTYLE'],
    datatypes: ['SMALLINT', 'INTEGER', 'BIGINT', 'DECIMAL', 'REAL', 'DOUBLE PRECISION', 'BOOLEAN'],
    weight: 1.0
  }
};

const MultiFileSQLInput: React.FC<MultiFileSQLInputProps> = ({ 
  onFilesChange, 
  onAnalysisComplete,
  targetDialect = 'postgresql'
}) => {
  const [files, setFiles] = useState<SQLFile[]>([]);
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [globalAnalysis, setGlobalAnalysis] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const editorRef = useRef(null);

  // Detect SQL dialect using AI API (with fallback to pattern matching)
  const detectDialectWithAI = async (content: string): Promise<DialectDetectionResult> => {
    try {
      // Call the backend AI detection API
      const response = await api.migration.detectDialect(content);
      
      if (response.success) {
        return {
          dialect: response.dialect,
          confidence: response.confidence,
          features: response.features || [],
          patterns: [`AI Detection: ${response.explanation}`]
        };
      } else {
        // Fallback to client-side detection
        return detectDialect(content);
      }
    } catch (error) {
      console.warn('AI dialect detection failed, using fallback pattern matching:', error);
      // Fallback to client-side detection
      return detectDialect(content);
    }
  };

  // Detect SQL dialect from content - Enhanced detection (FALLBACK ONLY)
  const detectDialect = (content: string): DialectDetectionResult => {
    const upperContent = content.toUpperCase();
    const scores: { [key: string]: { score: number; features: string[]; patterns: string[] } } = {};
    
    // Initialize scores for all dialects
    Object.keys(DIALECT_PATTERNS).forEach(dialect => {
      scores[dialect] = { score: 0, features: [], patterns: [] };
    });
    
    Object.entries(DIALECT_PATTERNS).forEach(([dialect, patterns]) => {
      let score = 0;
      const features: string[] = [];
      const matchedPatterns: string[] = [];
      
      // Check keywords (highest weight)
      patterns.keywords.forEach(keyword => {
        const regex = new RegExp(keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        const matches = (content.match(regex) || []).length;
        if (matches > 0) {
          score += matches * 5; // Increased weight for keywords
          features.push(keyword);
          matchedPatterns.push(`keyword: ${keyword}`);
        }
      });
      
      // Check functions
      patterns.functions.forEach(func => {
        const regex = new RegExp(func.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        const matches = (content.match(regex) || []).length;
        if (matches > 0) {
          score += matches * 3; // Increased weight for functions
          features.push(func);
          matchedPatterns.push(`function: ${func}`);
        }
      });
      
      // Check operators
      patterns.operators.forEach(op => {
        const regex = new RegExp(op.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        const matches = (content.match(regex) || []).length;
        if (matches > 0) {
          score += matches * 2; // Increased weight for operators
          features.push(op);
          matchedPatterns.push(`operator: ${op}`);
        }
      });
      
      // Check data types (if available)
      if (patterns.datatypes) {
        patterns.datatypes.forEach(datatype => {
          const regex = new RegExp(`\\b${datatype}\\b`, 'gi');
          const matches = (content.match(regex) || []).length;
          if (matches > 0) {
            score += matches * 3; // Added data type detection
            features.push(datatype);
            matchedPatterns.push(`datatype: ${datatype}`);
          }
        });
      }
      
      scores[dialect] = { 
        score: score * patterns.weight, 
        features, 
        patterns: matchedPatterns 
      };
    });
    
    // Find the dialect with the highest score
    const sortedDialects = Object.entries(scores).sort((a, b) => b[1].score - a[1].score);
    const bestMatch = sortedDialects[0];
    const secondBest = sortedDialects[1];
    
    // If no patterns matched, make an educated guess based on common SQL structure
    if (bestMatch[1].score === 0) {
      // Check for very basic indicators
      const hasBackticks = content.includes('`');
      const hasDoubleColon = content.includes('::');
      const hasSquareBrackets = /\[[\w\s]+\]/.test(content);
      const hasLimitClause = /\bLIMIT\s+\d+/i.test(content);
      
      let guessedDialect = 'mysql'; // Default guess
      let guessConfidence = 35; // Low but above threshold
      
      if (hasBackticks && hasLimitClause) {
        guessedDialect = 'mysql';
        guessConfidence = 40;
      } else if (hasDoubleColon) {
        guessedDialect = 'postgresql';
        guessConfidence = 40;
      } else if (hasSquareBrackets) {
        guessedDialect = 'mssql';
        guessConfidence = 40;
      } else if (content.includes('DUAL')) {
        guessedDialect = 'oracle';
        guessConfidence = 40;
      }
      
      return {
        dialect: guessedDialect,
        confidence: guessConfidence,
        features: ['basic SQL structure'],
        patterns: ['inferred from syntax']
      };
    }
    
    // Calculate confidence based on score difference
    const totalScore = Object.values(scores).reduce((sum, data) => sum + data.score, 0);
    let confidence = totalScore > 0 ? Math.min((bestMatch[1].score / totalScore) * 100, 95) : 0;
    
    // Boost confidence if there's a clear winner
    if (secondBest && bestMatch[1].score > secondBest[1].score * 1.5) {
      confidence = Math.min(confidence * 1.2, 95);
    }
    
    // Minimum confidence threshold lowered to 15 for better detection
    const finalDialect = confidence > 15 ? bestMatch[0] : 'mysql'; // Default to mysql if uncertain
    const finalConfidence = Math.max(Math.round(confidence), 25); // Ensure minimum 25% confidence
    
    return {
      dialect: finalDialect,
      confidence: finalConfidence,
      features: bestMatch[1].features.slice(0, 10), // Limit features shown
      patterns: bestMatch[1].patterns.slice(0, 10)  // Limit patterns shown
    };
  };

  // Analyze SQL content
  const analyzeSQLContent = async (content: string, fileName: string): Promise<SQLAnalysis> => {
    const lines = content.split('\n').filter(line => line.trim());
    const upperContent = content.toUpperCase();
    
    // Extract database objects
    const tableMatches = content.match(/(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)/gi) || [];
    const tables = [...new Set(tableMatches.map(match => 
      match.replace(/^(FROM|JOIN|INTO|UPDATE)\s+/i, '').trim().replace(/[`"[\]]/g, '')
    ))];
    
    const viewMatches = content.match(/CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([a-zA-Z_][a-zA-Z0-9_]*)/gi) || [];
    const views = viewMatches.map(match => 
      match.replace(/CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+/i, '').trim()
    );
    
    const procMatches = content.match(/CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+([a-zA-Z_][a-zA-Z0-9_]*)/gi) || [];
    const procedures = procMatches.map(match => 
      match.replace(/CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+/i, '').trim()
    );
    
    const funcMatches = content.match(/CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+([a-zA-Z_][a-zA-Z0-9_]*)/gi) || [];
    const functions = funcMatches.map(match => 
      match.replace(/CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+/i, '').trim()
    );
    
    const schemaMatches = content.match(/([a-zA-Z_][a-zA-Z0-9_]*)\.[a-zA-Z_][a-zA-Z0-9_]*/g) || [];
    const schemas = [...new Set(schemaMatches.map(match => match.split('.')[0]))];
    
    // Detect operations
    const operations = [];
    if (upperContent.includes('SELECT')) operations.push('SELECT');
    if (upperContent.includes('INSERT')) operations.push('INSERT');
    if (upperContent.includes('UPDATE')) operations.push('UPDATE');
    if (upperContent.includes('DELETE')) operations.push('DELETE');
    if (upperContent.includes('CREATE TABLE')) operations.push('CREATE TABLE');
    if (upperContent.includes('CREATE VIEW')) operations.push('CREATE VIEW');
    if (upperContent.includes('CREATE PROCEDURE')) operations.push('CREATE PROCEDURE');
    if (upperContent.includes('CREATE FUNCTION')) operations.push('CREATE FUNCTION');
    if (upperContent.includes('ALTER')) operations.push('ALTER');
    if (upperContent.includes('DROP')) operations.push('DROP');
    
    // Determine complexity
    let complexity: 'low' | 'medium' | 'high' = 'low';
    const complexityScore = 
      (content.match(/JOIN/gi) || []).length * 2 +
      (content.match(/SUBQUERY|EXISTS|CASE|WHEN/gi) || []).length * 3 +
      (content.match(/UNION|INTERSECT|EXCEPT/gi) || []).length * 2 +
      (content.match(/WITH\s+\w+\s+AS/gi) || []).length * 3 +
      tables.length +
      procedures.length * 4 +
      functions.length * 4;
    
    if (complexityScore > 25) complexity = 'high';
    else if (complexityScore > 10) complexity = 'medium';
    
    // Generate warnings and errors
    const warnings = [];
    const errors = [];
    
    if (content.includes('SELECT *')) {
      warnings.push('Consider specifying column names instead of SELECT *');
    }
    if (content.match(/WHERE.*=.*NULL/i)) {
      warnings.push('Use IS NULL instead of = NULL for null comparisons');
    }
    if (tables.length > 15) {
      warnings.push('High number of tables detected - consider breaking into smaller scripts');
    }
    if (content.match(/DROP\s+TABLE/gi)) {
      warnings.push('DROP TABLE statements detected - ensure proper backup before execution');
    }
    if (content.match(/TRUNCATE/gi)) {
      warnings.push('TRUNCATE statements detected - this will delete all data');
    }
    
    // Check for syntax errors (basic)
    if (content.match(/SELECT.*FROM(?!\s+\w)/gi)) {
      errors.push('Incomplete SELECT statement detected');
    }
    if (content.match(/\(\s*\)/g)) {
      warnings.push('Empty parentheses detected - check for incomplete statements');
    }
    
    // Detect dialect-specific features
    const dialectFeatures = [];
    const unsupportedFeatures = [];
    
    if (content.match(/AUTO_INCREMENT/gi)) dialectFeatures.push('AUTO_INCREMENT');
    if (content.match(/SERIAL/gi)) dialectFeatures.push('SERIAL');
    if (content.match(/IDENTITY\(/gi)) dialectFeatures.push('IDENTITY');
    if (content.match(/ENUM\(/gi)) dialectFeatures.push('ENUM');
    if (content.match(/JSON/gi)) dialectFeatures.push('JSON');
    
    // Estimate migration time
    let estimatedTime = '2-5 minutes';
    if (complexity === 'high' || lines.length > 1000) {
      estimatedTime = '30-60 minutes';
    } else if (complexity === 'medium' || lines.length > 300) {
      estimatedTime = '10-30 minutes';
    } else if (lines.length > 100) {
      estimatedTime = '5-15 minutes';
    }
    
    return {
      tables,
      views,
      procedures,
      functions,
      schemas,
      operations,
      complexity,
      warnings,
      errors,
      lineCount: lines.length,
      estimatedMigrationTime: estimatedTime,
      dialectFeatures,
      unsupportedFeatures
    };
  };

  // File upload handler
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const validExtensions = ['.sql', '.ddl', '.dml', '.txt'];
    const validFiles = acceptedFiles.filter(file => 
      validExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
    );
    
    if (validFiles.length !== acceptedFiles.length) {
      toast.error(`Only ${validExtensions.join(', ')} files are supported`);
    }
    
    if (validFiles.length === 0) return;
    
    const newFiles: SQLFile[] = validFiles.map(file => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: file.name,
      content: '',
      size: file.size,
      detectedDialect: 'unknown',
      confidence: 0,
      analysis: null,
      status: 'uploading',
      dependencies: [],
      uploadProgress: 0
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    
    // Process files sequentially
    for (let i = 0; i < validFiles.length; i++) {
      const file = validFiles[i];
      const fileId = newFiles[i].id;
      
      try {
        // Simulate upload progress
        for (let progress = 0; progress <= 100; progress += 20) {
          setFiles(prev => prev.map(f => 
            f.id === fileId ? { ...f, uploadProgress: progress } : f
          ));
          await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // Read file content
        const content = await file.text();
        
        // Update file with content
        setFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, content, status: 'analyzing' } : f
        ));
        
        // Detect dialect using AI
        const dialectResult = await detectDialectWithAI(content);
        
        // Analyze content
        const analysis = await analyzeSQLContent(content, file.name);
        
        // Update file with results
        setFiles(prev => prev.map(f => 
          f.id === fileId ? {
            ...f,
            detectedDialect: dialectResult.dialect,
            confidence: dialectResult.confidence,
            analysis,
            status: 'ready'
          } : f
        ));
        
        const detectionMethod = dialectResult.confidence >= 70 ? '?? AI-powered' : dialectResult.confidence >= 40 ? '?? AI' : '?? Pattern-based';
        toast.success(`${file.name} processed successfully`, {
          description: `${detectionMethod} detection: ${dialectResult.dialect.toUpperCase()} (${dialectResult.confidence}% confidence)`
        });
        
      } catch (error) {
        setFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'error', 
            error: 'Failed to process file' 
          } : f
        ));
        toast.error(`Failed to process ${file.name}`);
      }
    }
    
    // Update parent component
    const updatedFiles = files.concat(newFiles);
    onFilesChange(updatedFiles);
    
    // Switch to files tab
    setActiveTab('files');
  }, [files, onFilesChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.sql', '.ddl', '.dml', '.txt'],
      'application/sql': ['.sql']
    },
    maxSize: 50 * 1024 * 1024 // 50MB per file
  });

  // Remove file
  const removeFile = (fileId: string) => {
    const updatedFiles = files.filter(f => f.id !== fileId);
    setFiles(updatedFiles);
    onFilesChange(updatedFiles);
    
    if (selectedFile === fileId) {
      setSelectedFile(null);
    }
    
    toast.success('File removed');
  };

  // Analyze dependencies between files
  const analyzeDependencies = () => {
    const updatedFiles = files.map(file => {
      const dependencies: string[] = [];
      
      // Check if this file references objects from other files
      files.forEach(otherFile => {
        if (file.id !== otherFile.id && otherFile.analysis) {
          // Check if file references tables/views from other file
          const referencedTables = otherFile.analysis.tables.filter(table =>
            file.content.toLowerCase().includes(table.toLowerCase())
          );
          const referencedViews = otherFile.analysis.views.filter(view =>
            file.content.toLowerCase().includes(view.toLowerCase())
          );
          
          if (referencedTables.length > 0 || referencedViews.length > 0) {
            dependencies.push(otherFile.name);
          }
        }
      });
      
      return { ...file, dependencies };
    });
    
    setFiles(updatedFiles);
    onFilesChange(updatedFiles);
  };

  // Get file by ID
  const getFileById = (id: string) => files.find(f => f.id === id);
  
  // Get selected file
  const selectedFileData = selectedFile ? getFileById(selectedFile) : null;

  return (
    <Card className="enterprise-card">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Package className="h-5 w-5 mr-2" />
          Multi-File SQL Migration
        </CardTitle>
        <CardDescription>
          Upload multiple SQL files with automatic dialect detection and dependency analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload">Upload Files</TabsTrigger>
            <TabsTrigger value="files">
              Manage Files 
              {files.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {files.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="editor">SQL Editor</TabsTrigger>
            <TabsTrigger value="analysis">Global Analysis</TabsTrigger>
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
              
              <div>
                <p className="text-lg font-medium mb-2">
                  {isDragActive ? 'Drop your SQL files here' : 'Drag & drop multiple SQL files here'}
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  or click to browse files (.sql, .ddl, .dml, .txt up to 50MB each)
                </p>
                <Button variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Browse Files
                </Button>
              </div>
            </div>

            {files.length > 0 && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  {files.length} file{files.length > 1 ? 's' : ''} uploaded. 
                  Switch to "Manage Files" tab to view details.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="files" className="space-y-4">
            {files.length === 0 ? (
              <div className="text-center p-8 text-muted-foreground">
                <Folder className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="font-medium mb-2">No Files Uploaded</p>
                <p className="text-sm">
                  Upload SQL files to start the migration process
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Uploaded Files ({files.length})</h4>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm" onClick={analyzeDependencies}>
                      <ArrowRight className="h-4 w-4 mr-1" />
                      Analyze Dependencies
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-1" />
                      Download All
                    </Button>
                  </div>
                </div>

                <ScrollArea className="h-[400px] border rounded-lg p-4">
                  <div className="space-y-3">
                    {files.map((file, index) => (
                      <div key={file.id} className="border rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <FileCode className="h-5 w-5 text-primary" />
                            <div>
                              <p className="font-medium">{file.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {(file.size / 1024).toFixed(1)} KB
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <Badge variant={
                              file.status === 'ready' ? 'default' :
                              file.status === 'error' ? 'destructive' :
                              file.status === 'analyzing' ? 'secondary' :
                              'outline'
                            }>
                              {file.status === 'uploading' && <RefreshCw className="h-3 w-3 mr-1 animate-spin" />}
                              {file.status === 'analyzing' && <RefreshCw className="h-3 w-3 mr-1 animate-spin" />}
                              {file.status === 'ready' && <CheckCircle className="h-3 w-3 mr-1" />}
                              {file.status === 'error' && <AlertTriangle className="h-3 w-3 mr-1" />}
                              {file.status.toUpperCase()}
                            </Badge>
                            
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedFile(file.id)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => removeFile(file.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>

                        {file.status === 'uploading' && (
                          <Progress value={file.uploadProgress} className="h-2" />
                        )}

                        {file.status === 'ready' && file.analysis && (
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Dialect:</span>
                              <div className="flex items-center space-x-1">
                                <Badge variant="outline" className="text-xs">
                                  {file.detectedDialect.toUpperCase()}
                                </Badge>
                                <Badge 
                                  variant={file.confidence >= 70 ? "default" : "secondary"} 
                                  className="text-xs"
                                  title={file.confidence >= 70 ? "AI Detected with high confidence" : file.confidence >= 50 ? "AI Detected" : "Pattern Matching Fallback"}
                                >
                                  {file.confidence >= 70 ? '?? AI' : file.confidence >= 40 ? '??' : '??'}
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  {file.confidence}%
                                </span>
                              </div>
                            </div>
                            
                            <div>
                              <span className="text-muted-foreground">Tables:</span>
                              <p className="font-medium">{file.analysis.tables.length}</p>
                            </div>
                            
                            <div>
                              <span className="text-muted-foreground">Complexity:</span>
                              <Badge variant={
                                file.analysis.complexity === 'high' ? 'destructive' :
                                file.analysis.complexity === 'medium' ? 'default' : 'secondary'
                              } className="text-xs">
                                {file.analysis.complexity.toUpperCase()}
                              </Badge>
                            </div>
                            
                            <div>
                              <span className="text-muted-foreground">Dependencies:</span>
                              <p className="font-medium">{file.dependencies.length}</p>
                            </div>
                          </div>
                        )}

                        {file.dependencies.length > 0 && (
                          <div className="pt-2 border-t">
                            <p className="text-sm text-muted-foreground mb-2">Depends on:</p>
                            <div className="flex flex-wrap gap-1">
                              {file.dependencies.map(dep => (
                                <Badge key={dep} variant="outline" className="text-xs">
                                  {dep}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {file.error && (
                          <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>{file.error}</AlertDescription>
                          </Alert>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}
          </TabsContent>

          <TabsContent value="editor" className="space-y-4">
            {selectedFileData ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium">{selectedFileData.name}</h4>
                    <Badge variant="outline">
                      {selectedFileData.detectedDialect.toUpperCase()}
                    </Badge>
                    {selectedFileData.analysis && (
                      <Badge variant="secondary">
                        {selectedFileData.analysis.lineCount} lines
                      </Badge>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Select value={selectedFile || ''} onValueChange={setSelectedFile}>
                      <SelectTrigger className="w-48">
                        <SelectValue placeholder="Select file" />
                      </SelectTrigger>
                      <SelectContent>
                        {files.map(file => (
                          <SelectItem key={file.id} value={file.id}>
                            {file.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <Button variant="outline" size="sm">
                      <Zap className="h-4 w-4 mr-1" />
                      Format
                    </Button>
                    
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </Button>
                  </div>
                </div>

                <div className="border rounded-lg overflow-hidden">
                  <Editor
                    height="500px"
                    defaultLanguage="sql"
                    value={selectedFileData.content}
                    theme="vs-dark"
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      scrollBeyondLastLine: false,
                      fontSize: 14,
                      lineNumbers: 'on',
                      wordWrap: 'on',
                      automaticLayout: true
                    }}
                    onMount={(editor) => {
                      editorRef.current = editor;
                    }}
                  />
                </div>

                {selectedFileData.analysis && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card className="border border-border/50">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Overview</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Complexity:</span>
                          <Badge variant={
                            selectedFileData.analysis.complexity === 'high' ? 'destructive' :
                            selectedFileData.analysis.complexity === 'medium' ? 'default' : 'secondary'
                          }>
                            {selectedFileData.analysis.complexity.toUpperCase()}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Lines:</span>
                          <span className="font-medium">{selectedFileData.analysis.lineCount}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Migration Time:</span>
                          <span className="font-medium">{selectedFileData.analysis.estimatedMigrationTime}</span>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border border-border/50">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Database Objects</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Tables:</span>
                          <span className="font-medium">{selectedFileData.analysis.tables.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Views:</span>
                          <span className="font-medium">{selectedFileData.analysis.views.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Procedures:</span>
                          <span className="font-medium">{selectedFileData.analysis.procedures.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Functions:</span>
                          <span className="font-medium">{selectedFileData.analysis.functions.length}</span>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border border-border/50">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Quality Checks</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Warnings:</span>
                          <span className="font-medium text-warning">{selectedFileData.analysis.warnings.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Errors:</span>
                          <span className="font-medium text-destructive">{selectedFileData.analysis.errors.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Operations:</span>
                          <span className="font-medium">{selectedFileData.analysis.operations.length}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center p-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="font-medium mb-2">No File Selected</p>
                <p className="text-sm">
                  Select a file from the "Manage Files" tab to view its content
                </p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="analysis" className="space-y-4">
            {files.length === 0 ? (
              <div className="text-center p-8 text-muted-foreground">
                <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="font-medium mb-2">No Global Analysis Available</p>
                <p className="text-sm">
                  Upload SQL files to see comprehensive analysis across all files
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Migration Summary */}
                <Card className="border border-border/50">
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Database className="h-5 w-5 mr-2" />
                      Migration Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold">{files.length}</p>
                        <p className="text-sm text-muted-foreground">Total Files</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold">
                          {files.reduce((sum, f) => sum + (f.analysis?.tables.length || 0), 0)}
                        </p>
                        <p className="text-sm text-muted-foreground">Total Tables</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold">
                          {files.reduce((sum, f) => sum + (f.analysis?.lineCount || 0), 0)}
                        </p>
                        <p className="text-sm text-muted-foreground">Total Lines</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold">
                          {files.filter(f => f.status === 'ready').length}
                        </p>
                        <p className="text-sm text-muted-foreground">Ready for Migration</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Dialect Distribution */}
                <Card className="border border-border/50">
                  <CardHeader>
                    <CardTitle>Detected Dialects</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(
                        files.reduce((acc, file) => {
                          const dialect = file.detectedDialect || 'unknown';
                          acc[dialect] = (acc[dialect] || 0) + 1;
                          return acc;
                        }, {} as Record<string, number>)
                      ).map(([dialect, count]) => (
                        <div key={dialect} className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <Badge variant="outline">{dialect.toUpperCase()}</Badge>
                            <span className="text-sm">{count} file{count > 1 ? 's' : ''}</span>
                          </div>
                          <div className="flex-1 mx-4">
                            <div className="bg-muted rounded-full h-2">
                              <div 
                                className="bg-primary rounded-full h-2"
                                style={{ width: `${(count / files.length) * 100}%` }}
                              />
                            </div>
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {Math.round((count / files.length) * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Complexity Analysis */}
                <Card className="border border-border/50">
                  <CardHeader>
                    <CardTitle>Complexity Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {['low', 'medium', 'high'].map(complexity => {
                        const count = files.filter(f => f.analysis?.complexity === complexity).length;
                        return (
                          <div key={complexity} className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <Badge variant={
                                complexity === 'high' ? 'destructive' :
                                complexity === 'medium' ? 'default' : 'secondary'
                              }>
                                {complexity.toUpperCase()}
                              </Badge>
                              <span className="text-sm">{count} file{count !== 1 ? 's' : ''}</span>
                            </div>
                            <div className="flex-1 mx-4">
                              <div className="bg-muted rounded-full h-2">
                                <div 
                                  className={`rounded-full h-2 ${
                                    complexity === 'high' ? 'bg-destructive' :
                                    complexity === 'medium' ? 'bg-primary' : 'bg-secondary'
                                  }`}
                                  style={{ width: `${files.length > 0 ? (count / files.length) * 100 : 0}%` }}
                                />
                              </div>
                            </div>
                            <span className="text-sm text-muted-foreground">
                              {files.length > 0 ? Math.round((count / files.length) * 100) : 0}%
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Warnings and Issues */}
                {files.some(f => f.analysis && (f.analysis.warnings.length > 0 || f.analysis.errors.length > 0)) && (
                  <Card className="border border-border/50">
                    <CardHeader>
                      <CardTitle className="flex items-center text-warning">
                        <AlertTriangle className="h-5 w-5 mr-2" />
                        Issues Summary
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {files.map(file => {
                          if (!file.analysis || (file.analysis.warnings.length === 0 && file.analysis.errors.length === 0)) {
                            return null;
                          }
                          
                          return (
                            <div key={file.id} className="border rounded-lg p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium">{file.name}</span>
                                <div className="flex space-x-2">
                                  {file.analysis.errors.length > 0 && (
                                    <Badge variant="destructive">
                                      {file.analysis.errors.length} error{file.analysis.errors.length !== 1 ? 's' : ''}
                                    </Badge>
                                  )}
                                  {file.analysis.warnings.length > 0 && (
                                    <Badge variant="secondary">
                                      {file.analysis.warnings.length} warning{file.analysis.warnings.length !== 1 ? 's' : ''}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                              
                              <div className="space-y-1 text-sm">
                                {file.analysis.errors.map((error, index) => (
                                  <div key={index} className="flex items-start space-x-2 text-destructive">
                                    <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                    <span>{error}</span>
                                  </div>
                                ))}
                                {file.analysis.warnings.map((warning, index) => (
                                  <div key={index} className="flex items-start space-x-2 text-warning">
                                    <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                    <span>{warning}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default MultiFileSQLInput;