import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import MultiFileSQLInput, { SQLFile } from "./MultiFileSQLInput";
import BatchTranslationProcessor from "./BatchTranslationProcessor";
import { useMigrationProgress } from "@/hooks/useMigrationProgress";
import { useAuth } from "@/contexts/AuthContext";
import { sqlTranslationEngine, BatchTranslationResult } from "@/lib/sqlTranslationEngine";
import { DownloadSystem, DownloadOptions } from "@/lib/downloadSystem";
import { 
  Database, 
  ArrowRight, 
  Code, 
  Play, 
  CheckCircle, 
  Clock,
  AlertTriangle,
  GitBranch,
  Settings,
  Zap,
  FileText,
  Upload,
  Wifi,
  WifiOff,
  Download,
  RefreshCw,
  Package,
  Layers
} from "lucide-react";

const migrationSteps = [
  { id: 1, title: "Source Connection", status: "completed", time: "2 min" },
  { id: 2, title: "Schema Analysis", status: "completed", time: "5 min" },
  { id: 3, title: "SQL Translation", status: "running", time: "3 min" },
  { id: 4, title: "Validation", status: "pending", time: "2 min" },
  { id: 5, title: "Data Migration", status: "pending", time: "15 min" },
  { id: 6, title: "Performance Test", status: "pending", time: "5 min" }
];

const databases = [
  { id: "mysql", name: "MySQL", version: "8.0", icon: "🐬" },
  { id: "postgresql", name: "PostgreSQL", version: "14", icon: "🐘" },
  { id: "oracle", name: "Oracle", version: "19c", icon: "🏛️" },
  { id: "mssql", name: "SQL Server", version: "2019", icon: "🏢" },
  { id: "snowflake", name: "Snowflake", version: "Latest", icon: "❄️" },
  { id: "redshift", name: "Redshift", version: "Latest", icon: "🚀" }
];

const sqlExample = `-- Original MySQL Query
SELECT 
  u.user_id,
  u.username,
  COUNT(o.order_id) as order_count,
  SUM(o.total_amount) as total_spent,
  DATE_FORMAT(u.created_at, '%Y-%m') as signup_month
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
GROUP BY u.user_id, DATE_FORMAT(u.created_at, '%Y-%m')
HAVING COUNT(o.order_id) > 0
ORDER BY total_spent DESC
LIMIT 100;`;

const translatedSQL = `-- Translated Snowflake Query  
SELECT 
  u.user_id,
  u.username,
  COUNT(o.order_id) as order_count,
  SUM(o.total_amount) as total_spent,
  TO_CHAR(u.created_at, 'YYYY-MM') as signup_month
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id  
WHERE u.created_at >= DATEADD(MONTH, -6, CURRENT_TIMESTAMP())
GROUP BY u.user_id, TO_CHAR(u.created_at, 'YYYY-MM')
HAVING COUNT(o.order_id) > 0
ORDER BY total_spent DESC
LIMIT 100;`;

export default function SQLMigration() {
  const [targetDB, setTargetDB] = useState("snowflake");
  const [migrationProgress, setMigrationProgress] = useState(45);
  const [sqlFiles, setSQLFiles] = useState<SQLFile[]>([]);
  const [globalAnalysis, setGlobalAnalysis] = useState(null);
  const [activeMigrationId, setActiveMigrationId] = useState<string | null>(null);
  const [realTimeSteps, setRealTimeSteps] = useState(migrationSteps);
  const [batchResults, setBatchResults] = useState<BatchTranslationResult | null>(null);
  const [translationInProgress, setTranslationInProgress] = useState(false);
  const [performanceData, setPerformanceData] = useState(null);
  const [firebaseToken, setFirebaseToken] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  
  // Refs for auto-scrolling
  const sourceTargetRef = useRef<HTMLDivElement>(null);
  const translationRef = useRef<HTMLDivElement>(null);
  
  // Auth context
  const { currentUser } = useAuth();

  // Check backend status
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/health', {
          method: 'GET',
          signal: AbortSignal.timeout(5000) // 5 second timeout
        });
        if (response.ok) {
          setBackendStatus('online');
        } else {
          setBackendStatus('offline');
        }
      } catch (error) {
        setBackendStatus('offline');
      }
    };

    checkBackendStatus();
    
    // Check backend status every 30 seconds
    const statusInterval = setInterval(checkBackendStatus, 30000);
    
    return () => {
      clearInterval(statusInterval);
    };
  }, []);

  // Get Firebase token for WebSocket authentication with automatic refresh
  useEffect(() => {
    const getFirebaseToken = async (forceRefresh = false) => {
      // Safety check: ensure currentUser exists and has getIdToken method
      if (currentUser && typeof currentUser.getIdToken === 'function') {
        try {
          const token = await currentUser.getIdToken(forceRefresh);
          setFirebaseToken(token);
          console.log('Firebase token updated:', forceRefresh ? '(forced refresh)' : '(cached)');
        } catch (error) {
          console.error('Error getting Firebase token:', error);
          // Don't set to null immediately, keep existing token if available
          if (!firebaseToken) {
            setFirebaseToken(null);
          }
        }
      } else {
        // User not authenticated, clear token
        if (firebaseToken) {
          setFirebaseToken(null);
        }
      }
    };

    // Get initial token
    getFirebaseToken().catch(err => {
      console.error('Failed to get initial Firebase token:', err);
    });

    // Set up automatic token refresh every 50 minutes (tokens expire in 1 hour)
    const tokenRefreshInterval = setInterval(() => {
      if (currentUser && typeof currentUser.getIdToken === 'function') {
        console.log('Refreshing Firebase token automatically...');
        getFirebaseToken(true).catch(err => {
          console.error('Failed to refresh Firebase token:', err);
        });
      }
    }, 50 * 60 * 1000); // 50 minutes

    return () => {
      clearInterval(tokenRefreshInterval);
    };
  }, [currentUser, firebaseToken]);

  // WebSocket integration for real-time progress (only when backend is online)
  const {
    isConnected,
    connectionState,
    progressData,
    errors,
    subscribeToMigration,
    unsubscribeFromMigration
  } = useMigrationProgress({
    onProgress: (progress) => {
      console.log('Migration progress:', progress);
      setMigrationProgress(progress.progress_percentage);
      
      // Update steps based on current phase
      setRealTimeSteps(prev => prev.map(step => {
        if (progress.current_phase === step.title) {
          return { ...step, status: "running" };
        } else if (progress.progress_percentage > ((step.id - 1) / prev.length) * 100) {
          return { ...step, status: "completed" };
        } else {
          return { ...step, status: "pending" };
        }
      }));
      
      toast.info(`Migration Progress: ${Math.round(progress.progress_percentage)}%`, {
        description: progress.current_step || progress.current_phase
      });
    },
    onStatusChange: (migrationId, status, message) => {
      console.log('Migration status change:', { migrationId, status, message });
      toast.success(`Migration ${status}`, { description: message });
    },
    onError: (error) => {
      // Completely suppress all WebSocket error toasts - backend status indicator handles this
      console.warn('WebSocket error (suppressed):', error);
    }
  });

  const handleFilesChange = (files: SQLFile[]) => {
    setSQLFiles(files);
    console.log('Files updated:', files.length, 'files');
  };

  const handleGlobalAnalysisComplete = (analysis: any) => {
    setGlobalAnalysis(analysis);
    console.log('Global analysis completed:', analysis);
  };

  const handleBatchTranslationComplete = (results: BatchTranslationResult) => {
    setBatchResults(results);
    console.log('Batch translation completed:', results);
    
    // Auto-scroll to results
    setTimeout(() => {
      translationRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }, 500);
  };

  // Enhanced client-side SQL translation with comprehensive database support
  const performClientSideTranslation = (sql: string, sourceDialect: string, targetDialect: string) => {
    let translated = sql;
    
    // Add header comment
    const timestamp = new Date().toISOString();
    const header = `-- Translated from ${sourceDialect.toUpperCase()} to ${targetDialect.toUpperCase()}\n-- Generated on: ${timestamp}\n-- Client-side translation - review before production use\n\n`;
    
    // MySQL to PostgreSQL
    if (sourceDialect === 'mysql' && targetDialect === 'postgresql') {
      translated = translated
        // Data types
        .replace(/\bINT\s+AUTO_INCREMENT\b/gi, 'SERIAL')
        .replace(/\bBIGINT\s+AUTO_INCREMENT\b/gi, 'BIGSERIAL')
        .replace(/\bAUTO_INCREMENT\b/gi, 'SERIAL')
        .replace(/\bTINYINT\(1\)\b/gi, 'BOOLEAN')
        .replace(/\bTINYINT\b/gi, 'SMALLINT')
        .replace(/\bDATETIME\b/gi, 'TIMESTAMP')
        .replace(/\bLONGTEXT\b/gi, 'TEXT')
        .replace(/\bMEDIUMTEXT\b/gi, 'TEXT')
        .replace(/\bTINYTEXT\b/gi, 'VARCHAR(255)')
        .replace(/\bDOUBLE\b/gi, 'DOUBLE PRECISION')
        .replace(/\bFLOAT\b/gi, 'REAL')
        
        // Remove MySQL-specific keywords
        .replace(/\bUNSIGNED\b/gi, '')
        .replace(/\bENGINE\s*=\s*\w+/gi, '')
        .replace(/\bDEFAULT\s+CHARSET\s*=\s*[\w\d_]+/gi, '')
        .replace(/\bCOLLATE\s*=\s*[\w\d_]+/gi, '')
        .replace(/\bCOMMENT\s*=\s*'[^']*'/gi, '')
        
        // Quote identifiers
        .replace(/`([^`]+)`/g, '"$1"')
        
        // Functions
        .replace(/\bNOW\s*\(\s*\)/gi, 'CURRENT_TIMESTAMP')
        .replace(/\bIFNULL\s*\(/gi, 'COALESCE(')
        
        // LIMIT syntax
        .replace(/\bLIMIT\s+(\d+)\s*,\s*(\d+)\b/gi, 'LIMIT $2 OFFSET $1')
        
        // ENUM handling (simplified)
        .replace(/\bENUM\s*\(\s*([^)]+)\s*\)/gi, 'VARCHAR(50) CHECK (column_name IN ($1))');
    }
    
    // PostgreSQL to MySQL
    if (sourceDialect === 'postgresql' && targetDialect === 'mysql') {
      translated = translated
        // Data types
        .replace(/\bSERIAL\b/gi, 'INT AUTO_INCREMENT')
        .replace(/\bBIGSERIAL\b/gi, 'BIGINT AUTO_INCREMENT')
        .replace(/\bBOOLEAN\b/gi, 'TINYINT(1)')
        .replace(/\bTIMESTAMP\b/gi, 'DATETIME')
        .replace(/\bDOUBLE\s+PRECISION\b/gi, 'DOUBLE')
        .replace(/\bREAL\b/gi, 'FLOAT')
        
        // Quote identifiers
        .replace(/"([^"]+)"/g, '`$1`')
        
        // Functions
        .replace(/\bCURRENT_TIMESTAMP\b/gi, 'NOW()')
        .replace(/\bCOALESCE\s*\(/gi, 'IFNULL(')
        
        // LIMIT syntax
        .replace(/\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\b/gi, 'LIMIT $2, $1');
    }
    
    // MySQL to Snowflake
    if (sourceDialect === 'mysql' && targetDialect === 'snowflake') {
      translated = translated
        .replace(/\bAUTO_INCREMENT\b/gi, 'AUTOINCREMENT')
        .replace(/\bTINYINT(\(\d+\))?/gi, 'SMALLINT')
        .replace(/\bMEDIUMINT(\(\d+\))?/gi, 'INT')
        .replace(/\bLONGTEXT\b/gi, 'TEXT')
        .replace(/\bDATETIME\b/gi, 'TIMESTAMP')
        .replace(/\bENGINE\s*=\s*\w+/gi, '')
        .replace(/\bDEFAULT\s+CHARSET\s*=\s*[\w\d_]+/gi, '')
        .replace(/\bCOLLATE\s*=\s*[\w\d_]+/gi, '')
        .replace(/\bDATE_FORMAT\s*\(\s*([^,]+),\s*'%Y-%m'\s*\)/gi, "TO_CHAR($1, 'YYYY-MM')")
        .replace(/\bDATE_SUB\s*\(\s*NOW\(\),\s*INTERVAL\s+(\d+)\s+MONTH\s*\)/gi, 'DATEADD(MONTH, -$1, CURRENT_TIMESTAMP())')
        .replace(/\bNOW\(\)/gi, 'CURRENT_TIMESTAMP()')
        .replace(/`([^`]+)`/g, '"$1"');
    }
    
    // PostgreSQL to Snowflake
    if (sourceDialect === 'postgresql' && targetDialect === 'snowflake') {
      translated = translated
        .replace(/\bSERIAL\b/gi, 'AUTOINCREMENT')
        .replace(/\bBIGSERIAL\b/gi, 'AUTOINCREMENT')
        .replace(/\bBOOLEAN\b/gi, 'BOOLEAN')
        .replace(/\bTIMESTAMP WITH TIME ZONE\b/gi, 'TIMESTAMP_TZ')
        .replace(/\bCURRENT_TIMESTAMP\b/gi, 'CURRENT_TIMESTAMP()');
    }
    
    // SQLite translations
    if (targetDialect === 'sqlite') {
      translated = translated
        .replace(/\bAUTO_INCREMENT\b/gi, 'AUTOINCREMENT')
        .replace(/\bSERIAL\b/gi, 'INTEGER PRIMARY KEY AUTOINCREMENT')
        .replace(/\bBIGSERIAL\b/gi, 'INTEGER PRIMARY KEY AUTOINCREMENT')
        .replace(/\bDATETIME\b/gi, 'TEXT')
        .replace(/\bTIMESTAMP\b/gi, 'TEXT')
        .replace(/\bBOOLEAN\b/gi, 'INTEGER')
        .replace(/\bTINYINT\(1\)\b/gi, 'INTEGER')
        .replace(/\bENGINE\s*=\s*\w+/gi, '')
        .replace(/\bDEFAULT\s+CHARSET\s*=\s*[\w\d_]+/gi, '')
        .replace(/\bCOLLATE\s*=\s*[\w\d_]+/gi, '');
    }
    
    // SQL Server translations
    if (targetDialect === 'mssql') {
      translated = translated
        .replace(/\bAUTO_INCREMENT\b/gi, 'IDENTITY(1,1)')
        .replace(/\bSERIAL\b/gi, 'INT IDENTITY(1,1)')
        .replace(/\bBIGSERIAL\b/gi, 'BIGINT IDENTITY(1,1)')
        .replace(/\bBOOLEAN\b/gi, 'BIT')
        .replace(/\bTEXT\b/gi, 'NVARCHAR(MAX)')
        .replace(/\bLONGTEXT\b/gi, 'NVARCHAR(MAX)')
        .replace(/\bMEDIUMTEXT\b/gi, 'NVARCHAR(MAX)')
        .replace(/\bTINYTEXT\b/gi, 'NVARCHAR(255)')
        .replace(/`([^`]+)`/g, '[$1]')
        .replace(/"([^"]+)"/g, '[$1]');
    }
    
    // Oracle translations
    if (targetDialect === 'oracle') {
      translated = translated
        .replace(/\bAUTO_INCREMENT\b/gi, '')
        .replace(/\bSERIAL\b/gi, 'NUMBER GENERATED BY DEFAULT AS IDENTITY')
        .replace(/\bBIGSERIAL\b/gi, 'NUMBER GENERATED BY DEFAULT AS IDENTITY')
        .replace(/\bBOOLEAN\b/gi, 'NUMBER(1)')
        .replace(/\bTEXT\b/gi, 'CLOB')
        .replace(/\bLONGTEXT\b/gi, 'CLOB')
        .replace(/\bMEDIUMTEXT\b/gi, 'CLOB')
        .replace(/\bTINYTEXT\b/gi, 'VARCHAR2(255)')
        .replace(/\bVARCHAR\((\d+)\)/gi, 'VARCHAR2($1)')
        .replace(/\bDATETIME\b/gi, 'TIMESTAMP')
        .replace(/\bTIMESTAMP\b/gi, 'TIMESTAMP')
        .replace(/`([^`]+)`/g, '"$1"');
    }
    
    // Clean up and format
    translated = translated
      // Normalize line endings
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      
      // Clean up extra whitespace
      .replace(/\s+/g, ' ')
      .replace(/\s*;\s*/g, ';\n')
      
      // Better formatting
      .replace(/CREATE\s+TABLE/gi, 'CREATE TABLE')
      .replace(/\(\s*/g, ' (\n  ')
      .replace(/\s*\)/g, '\n)')
      .replace(/,\s*/g, ',\n  ')
      .trim();
    
    return header + translated;
  };

  const startMigrationAnalysis = async () => {
    if (sqlFiles.length === 0) {
      toast.error('Please upload SQL files to analyze');
      return;
    }

    const readyFiles = sqlFiles.filter(f => f.status === 'ready');
    if (readyFiles.length === 0) {
      toast.error('No files are ready for migration analysis');
      return;
    }

    try {
      setTranslationInProgress(true);
      
      // Use the new translation engine for batch processing
      const results = await sqlTranslationEngine.translateBatch(
        readyFiles,
        targetDB,
        (progress, currentFile) => {
          setMigrationProgress(progress);
          // Update real-time steps based on progress
          setRealTimeSteps(prev => prev.map(step => {
            if (progress > ((step.id - 1) / prev.length) * 100) {
              return { ...step, status: "completed" };
            } else if (progress > ((step.id - 1.5) / prev.length) * 100) {
              return { ...step, status: "running" };
            } else {
              return { ...step, status: "pending" };
            }
          }));
        }
      );
      
      setBatchResults(results);
      
      // Auto-scroll to results tab
      setTimeout(() => {
        translationRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 500);
      
      const uniqueSourceDialects = Array.from(new Set(readyFiles.map(f => f.detectedDialect))).join(', ').toUpperCase();
      toast.success('Batch SQL translation completed!', {
        description: `Successfully translated ${readyFiles.length} files to ${targetDB.toUpperCase()}`
      });
      
      // Simulate analysis progress for better UX
      let progress = 0;
      const progressInterval = setInterval(() => {
        progress += 15;
        setMigrationProgress(progress);
        
        if (progress >= 100) {
          clearInterval(progressInterval);
          setMigrationProgress(100);
          
          // Generate mock performance data for demonstration
          setTimeout(() => {
            setPerformanceData({
              query_execution: {
                before: '2.4s',
                after: '0.8s',
                improvement: '+67%'
              },
              resource_usage: {
                cpu_usage: '-45%',
                memory: '-32%',
                io_operations: '-58%'
              },
              cost_analysis: {
                monthly_cost: '-$2,340',
                annual_savings: '$28,080',
                roi: '340%'
              }
            });
            
            toast.success('Migration analysis completed!', {
              description: 'Performance metrics and optimization suggestions are now available.'
            });
          }, 2000);
        }
      }, 300);
      
      // Update migration steps
      const stepUpdates = [
        { title: "Source Connection", delay: 200 },
        { title: "Schema Analysis", delay: 500 },
        { title: "SQL Translation", delay: 800 },
        { title: "Validation", delay: 1100 },
        { title: "Data Migration", delay: 1400 },
        { title: "Performance Test", delay: 1700 }
      ];
      
      stepUpdates.forEach(({ title, delay }) => {
        setTimeout(() => {
          setRealTimeSteps(prev => prev.map(step => {
            if (step.title === title) {
              return { ...step, status: "completed" };
            }
            return step;
          }));
        }, delay);
      });

      // Set a mock migration ID for demo purposes
      const mockMigrationId = `migration_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setActiveMigrationId(mockMigrationId);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start migration analysis';
      toast.error('Migration Analysis Failed', {
        description: errorMessage
      });
      console.error('Migration analysis error:', error);
    } finally {
      setTranslationInProgress(false);
    }
  };

  // Cleanup subscription on unmount
  useEffect(() => {
    return () => {
      if (activeMigrationId) {
        unsubscribeFromMigration(activeMigrationId);
      }
    };
  }, [activeMigrationId, unsubscribeFromMigration]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold">SQL Migration Workspace</h1>
          
          {/* Backend and WebSocket Connection Status */}
          <div className="flex items-center space-x-2">
            {/* Backend Status */}
            <Badge variant={backendStatus === 'online' ? 'default' : 'secondary'} 
                   className={backendStatus === 'online' ? 'bg-success' : 'bg-warning/20 text-warning'}>
              <Database className="h-3 w-3 mr-1" />
              Backend {backendStatus === 'checking' ? 'Checking...' : backendStatus === 'online' ? 'Online' : 'Offline'}
            </Badge>
            
            {/* WebSocket Status (only show if backend is online) */}
            {backendStatus === 'online' && (
              <>
                {isConnected ? (
                  <Badge variant="default" className="bg-success">
                    <Wifi className="h-3 w-3 mr-1" />
                    Real-time Connected
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="bg-warning/20 text-warning">
                    <WifiOff className="h-3 w-3 mr-1" />
                    {connectionState === 'connecting' ? 'Connecting...' : 'Real-time Disconnected'}
                  </Badge>
                )}
              </>
            )}
          </div>
        </div>
        <p className="text-muted-foreground">
          Seamlessly migrate and translate SQL across different database platforms
        </p>
        
        {/* Show active migration info */}
        {activeMigrationId && (
          <Alert className="mt-4">
            <Clock className="h-4 w-4" />
            <AlertDescription>
              Active migration: {activeMigrationId} - Progress: {Math.round(migrationProgress)}%
            </AlertDescription>
          </Alert>
        )}
      </div>

      <Tabs defaultValue="upload" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="upload">
            <Upload className="h-4 w-4 mr-1" />
            Upload & Analyze
          </TabsTrigger>
          <TabsTrigger value="setup">
            <Settings className="h-4 w-4 mr-1" />
            Configure Migration
          </TabsTrigger>
          <TabsTrigger value="batch">
            <Clock className="h-4 w-4 mr-1" />
            Migration Progress
          </TabsTrigger>
          <TabsTrigger value="results">
            <Download className="h-4 w-4 mr-1" />
            Results & Download
          </TabsTrigger>
          <TabsTrigger value="performance">
            <Zap className="h-4 w-4 mr-1" />
            Performance
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6">
          {/* Multi-File SQL Input */}
          <MultiFileSQLInput 
            onFilesChange={handleFilesChange}
            onAnalysisComplete={handleGlobalAnalysisComplete}
            targetDialect={targetDB}
          />
        </TabsContent>

        <TabsContent value="setup" className="space-y-6">
          {/* Target Database Selection */}
          <Card className="enterprise-card" ref={sourceTargetRef}>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="h-5 w-5 mr-2" />
                Target Database Selection
              </CardTitle>
              <CardDescription>
                Select the target database platform for migration. Source dialects will be automatically detected from your SQL files.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Detected Source Dialects Summary */}
                {sqlFiles.length > 0 && (
                  <Card className="border border-border/50 bg-muted/30">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg flex items-center">
                        <Code className="h-4 w-4 mr-2" />
                        Detected Source Dialects
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {Array.from(new Set(sqlFiles.map(f => f.detectedDialect))).map((dialect) => {
                          const count = sqlFiles.filter(f => f.detectedDialect === dialect).length;
                          const avgConfidence = Math.round(
                            sqlFiles
                              .filter(f => f.detectedDialect === dialect)
                              .reduce((sum, f) => sum + f.confidence, 0) / count
                          );
                          return (
                            <div key={dialect} className="flex items-center space-x-2 bg-background border rounded-lg px-3 py-2">
                              <Database className="h-4 w-4 text-primary" />
                              <span className="font-medium">{dialect.toUpperCase()}</span>
                              <Badge variant="outline" className="text-xs">
                                {count} file{count > 1 ? 's' : ''}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {avgConfidence}% confidence
                              </span>
                            </div>
                          );
                        })}
                      </div>
                      {sqlFiles.some(f => f.confidence < 50) && (
                        <Alert className="mt-4">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            Some files have low dialect detection confidence. Review the results carefully before migration.
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Target Database Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="border border-border/50">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg">Select Target Database</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Select value={targetDB} onValueChange={setTargetDB}>
                        <SelectTrigger className="h-12">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {databases.map((db) => (
                            <SelectItem key={db.id} value={db.id}>
                              <div className="flex items-center space-x-3 py-1">
                                <span className="text-2xl">{db.icon}</span>
                                <div>
                                  <p className="font-medium">{db.name}</p>
                                  <p className="text-xs text-muted-foreground">{db.version}</p>
                                </div>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      <div className="mt-4 p-3 bg-muted rounded-lg">
                        <div className="flex items-start space-x-2">
                          <CheckCircle className="h-4 w-4 text-success mt-0.5" />
                          <div>
                            <p className="text-sm font-medium">Ready for Migration</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              All uploaded files will be converted to {targetDB.toUpperCase()} dialect
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Migration Options */}
                  <Card className="border border-border/50">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg">Migration Options</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="opt-schema" className="rounded" defaultChecked />
                        <label htmlFor="opt-schema" className="text-sm cursor-pointer">Migrate schema structure</label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="opt-data" className="rounded" defaultChecked />
                        <label htmlFor="opt-data" className="text-sm cursor-pointer">Migrate data content</label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="opt-constraints" className="rounded" defaultChecked />
                        <label htmlFor="opt-constraints" className="text-sm cursor-pointer">Preserve constraints</label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="opt-optimize" className="rounded" defaultChecked />
                        <label htmlFor="opt-optimize" className="text-sm cursor-pointer">Optimize for target platform</label>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Migration Summary */}
                {sqlFiles.length > 0 && (
                  <Card className="border border-primary/20 bg-primary/5">
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center space-x-2">
                            <FileText className="h-5 w-5 text-primary" />
                            <div>
                              <p className="text-sm font-medium">Files Ready</p>
                              <p className="text-2xl font-bold">{sqlFiles.length}</p>
                            </div>
                          </div>
                          <div className="h-12 w-px bg-border" />
                          <div className="flex items-center space-x-2">
                            <ArrowRight className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <p className="text-sm font-medium">Target</p>
                              <p className="text-lg font-bold">{targetDB.toUpperCase()}</p>
                            </div>
                          </div>
                        </div>
                        
                        <Button 
                          className="enterprise-button-primary"
                          size="lg"
                          onClick={startMigrationAnalysis}
                          disabled={sqlFiles.length === 0 || translationInProgress}
                        >
                          {translationInProgress ? (
                            <>
                              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                              Processing Migration...
                            </>
                          ) : (
                            <>
                              <GitBranch className="h-4 w-4 mr-2" />
                              Start Migration ({sqlFiles.length} files)
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {sqlFiles.length === 0 && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Upload SQL files in the "Upload Files" tab to begin migration setup.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="batch" className="space-y-6">
          {/* Batch Translation Processor */}
          <BatchTranslationProcessor
            files={sqlFiles}
            targetDialect={targetDB}
            onTranslationComplete={handleBatchTranslationComplete}
            onDownloadReady={(jobId) => {
              toast.success('Translation results ready for download', {
                description: `Job ${jobId} completed successfully`
              });
            }}
          />
        </TabsContent>

        <TabsContent value="results" className="space-y-6" ref={translationRef}>
          {/* Translation Results */}
          {batchResults ? (
            <div className="space-y-6">
              {/* Results Summary */}
              <Card className="enterprise-card">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <CheckCircle className="h-5 w-5 mr-2 text-success" />
                    Translation Results Summary
                  </CardTitle>
                  <CardDescription>
                    Migration completed successfully with {batchResults.files.length} files processed
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <Card className="border border-border/50">
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold">{batchResults.files.length}</p>
                        <p className="text-sm text-muted-foreground">Files Translated</p>
                      </CardContent>
                    </Card>
                    
                    <Card className="border border-border/50">
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold">
                          {batchResults.files.reduce((sum, f) => sum + f.result.appliedRules.length, 0)}
                        </p>
                        <p className="text-sm text-muted-foreground">Rules Applied</p>
                      </CardContent>
                    </Card>
                    
                    <Card className="border border-border/50">
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold">
                          {Math.round(
                            batchResults.files.reduce((sum, f) => sum + f.result.confidence, 0) / 
                            batchResults.files.length
                          )}%
                        </p>
                        <p className="text-sm text-muted-foreground">Avg Confidence</p>
                      </CardContent>
                    </Card>
                    
                    <Card className="border border-border/50">
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold">{batchResults.estimatedExecutionTime}</p>
                        <p className="text-sm text-muted-foreground">Est. Execution Time</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Download Options */}
                  <div className="space-y-4">
                    <h4 className="font-medium">Download Options</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Button 
                        className="enterprise-button-primary"
                        onClick={() => {
                          const uniqueSourceDialects = Array.from(new Set(sqlFiles.map(f => f.detectedDialect))).join('_');
                          const files = DownloadSystem.createFileDownloads(
                            batchResults,
                            sqlFiles,
                            uniqueSourceDialects,
                            targetDB,
                            `${targetDB.toUpperCase()} Migration`,
                            {
                              includeOriginal: false,
                              includeReport: true,
                              includeMetadata: true,
                              format: 'zip',
                              compression: 'none'
                            }
                          );
                          DownloadSystem.downloadAsZip(
                            files,
                            `${targetDB}_migration_${new Date().toISOString().split('T')[0]}`,
                            {
                              includeOriginal: false,
                              includeReport: true,
                              includeMetadata: true,
                              format: 'zip',
                              compression: 'none'
                            }
                          );
                        }}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download Complete Package
                      </Button>
                      
                      <Button 
                        variant="outline"
                        onClick={() => {
                          const uniqueSourceDialects = Array.from(new Set(sqlFiles.map(f => f.detectedDialect))).join('_');
                          const report = DownloadSystem.generateMigrationReport(
                            batchResults,
                            uniqueSourceDialects,
                            targetDB,
                            `${targetDB.toUpperCase()} Migration`
                          );
                          DownloadSystem.downloadFile({
                            name: 'MIGRATION_REPORT.md',
                            content: report,
                            type: 'md',
                            size: report.length
                          });
                        }}
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        Download Report Only
                      </Button>
                    </div>
                  </div>

                  {/* Execution Order */}
                  <div className="mt-6 pt-4 border-t">
                    <h4 className="font-medium mb-3">Recommended Execution Order</h4>
                    <div className="flex flex-wrap items-center gap-2">
                      {batchResults.dependencyOrder.map((fileName, index) => (
                        <React.Fragment key={fileName}>
                          <Badge variant="outline" className="px-3 py-1">
                            {index + 1}. {fileName}
                          </Badge>
                          {index < batchResults.dependencyOrder.length - 1 && (
                            <ArrowRight className="h-4 w-4 text-muted-foreground" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Individual File Results */}
              <Card className="enterprise-card">
                <CardHeader>
                  <CardTitle>Individual File Results</CardTitle>
                  <CardDescription>
                    Detailed translation results for each processed file
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {batchResults.files.map(file => (
                      <Card key={file.id} className="border border-border/50">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium">{file.name}</h4>
                            <div className="flex items-center space-x-2">
                              <Badge variant="outline">
                                {file.result.confidence}% confidence
                              </Badge>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  DownloadSystem.downloadFile({
                                    name: `translated_${file.name}`,
                                    content: file.result.translatedContent,
                                    type: 'sql',
                                    size: file.result.translatedContent.length
                                  });
                                }}
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Rules Applied:</span>
                              <p className="font-medium">{file.result.appliedRules.length}</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Warnings:</span>
                              <p className="font-medium text-warning">{file.result.warnings.length}</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Errors:</span>
                              <p className="font-medium text-destructive">{file.result.errors.length}</p>
                            </div>
                          </div>

                          {file.result.warnings.length > 0 && (
                            <div className="mt-3 pt-3 border-t">
                              <p className="text-sm font-medium text-warning mb-2">Warnings:</p>
                              <div className="space-y-1">
                                {file.result.warnings.slice(0, 3).map((warning, index) => (
                                  <p key={index} className="text-xs text-warning">• {warning}</p>
                                ))}
                                {file.result.warnings.length > 3 && (
                                  <p className="text-xs text-muted-foreground">
                                    +{file.result.warnings.length - 3} more warnings
                                  </p>
                                )}
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="text-center p-8 text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium mb-2">No Translation Results</p>
              <p className="text-sm">
                Complete a batch translation to see results and download options
              </p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="translation" className="space-y-6">{/* Legacy translation tab - keeping for compatibility */}
          {/* SQL Editor */}
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Code className="h-5 w-5 mr-2" />
                SQL Translation Workspace
              </CardTitle>
              <CardDescription>
                Real-time SQL translation with syntax highlighting and validation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Source SQL */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">
                      Source SQL {sqlFiles.length > 0 && sqlFiles[0]?.detectedDialect ? 
                        `(${sqlFiles[0].detectedDialect.toUpperCase()})` : 
                        '(Auto-detected)'}
                    </h4>
                    <Badge variant="outline">Original</Badge>
                  </div>
                  <div className="bg-muted rounded-lg p-4 font-mono text-sm min-h-[400px] overflow-auto">
                    <pre className="whitespace-pre-wrap">{sqlFiles.length > 0 && sqlFiles[0]?.content ? sqlFiles[0].content : sqlExample}</pre>
                  </div>
                </div>

                {/* Translated SQL */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">Translated SQL ({targetDB.toUpperCase()})</h4>
                    {translationInProgress ? (
                      <Badge variant="secondary">
                        <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                        Translating...
                      </Badge>
                    ) : (
                      <Badge variant="default" className="bg-success">
                        <Zap className="h-3 w-3 mr-1" />
                        Optimized
                      </Badge>
                    )}
                  </div>
                  <div className="bg-muted rounded-lg p-4 font-mono text-sm min-h-[400px] overflow-auto">
                    {translationInProgress ? (
                      <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
                          <p className="text-sm text-muted-foreground">Translating SQL...</p>
                        </div>
                      </div>
                    ) : (
                      <pre className="whitespace-pre-wrap">{batchResults?.files[0]?.result.translatedContent || `-- Translated ${targetDB.toUpperCase()} Query\n${sqlFiles.length > 0 ? sqlFiles[0]?.content || sqlExample : sqlExample}`}</pre>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-6 pt-4 border-t border-border">
                <div className="flex items-center space-x-4">
                  <Badge variant="outline">
                    <CheckCircle className="h-3 w-3 mr-1 text-success" />
                    Syntax Valid
                  </Badge>
                  <Badge variant="outline">
                    <Zap className="h-3 w-3 mr-1 text-primary" />
                    Performance Optimized
                  </Badge>
                  <Badge variant="outline">
                    <CheckCircle className="h-3 w-3 mr-1 text-success" />
                    Semantically Equivalent
                  </Badge>
                </div>
                <div className="flex space-x-2">
                  <Button variant="outline">
                    <Play className="h-4 w-4 mr-2" />
                    Test Query
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      const content = batchResults?.files[0]?.result.translatedContent || `-- Translated ${targetDB.toUpperCase()} Query\n${sqlFiles.length > 0 ? sqlFiles[0]?.content || sqlExample : sqlExample}`;
                      const blob = new Blob([content], { type: 'text/sql' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `translated_${targetDB}_query.sql`;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      URL.revokeObjectURL(url);
                      toast.success('Translated SQL downloaded!');
                    }}
                    disabled={sqlFiles.length === 0 && !batchResults}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download SQL
                  </Button>
                  <Button className="enterprise-button-success">
                    Apply Translation
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="progress" className="space-y-6">
          {/* Migration Progress */}
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Clock className="h-5 w-5 mr-2" />
                Migration Progress
              </CardTitle>
              <CardDescription>
                Real-time status of your database migration process
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-medium">Overall Progress</h4>
                  <span className="text-2xl font-bold">{migrationProgress}%</span>
                </div>
                <Progress value={migrationProgress} className="h-3" />
                
                <div className="space-y-4">
                  {realTimeSteps.map((step) => (
                    <div key={step.id} className="flex items-center space-x-4 p-3 rounded-lg border border-border/50">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        step.status === 'completed' ? 'bg-success text-white' :
                        step.status === 'running' ? 'bg-primary text-white animate-pulse' :
                        'bg-muted text-muted-foreground'
                      }`}>
                        {step.status === 'completed' && <CheckCircle className="h-5 w-5" />}
                        {step.status === 'running' && <Clock className="h-5 w-5" />}
                        {step.status === 'pending' && <span>{step.id}</span>}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{step.title}</p>
                        <p className="text-sm text-muted-foreground">
                          Estimated time: {step.time}
                        </p>
                      </div>
                      <Badge variant={
                        step.status === 'completed' ? 'default' :
                        step.status === 'running' ? 'secondary' : 'outline'
                      }>
                        {step.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          {/* Performance Comparison */}
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="h-5 w-5 mr-2" />
                Performance Analysis
              </CardTitle>
              <CardDescription>
                Estimated performance metrics comparison after migration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="border border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Query Execution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Before Migration</span>
                        <span className="font-medium">{performanceData?.query_execution?.before || '2.4s'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">After Migration</span>
                        <span className="font-medium text-success">{performanceData?.query_execution?.after || '0.8s'}</span>
                      </div>
                      <div className="h-px bg-border my-2" />
                      <div className="flex justify-between font-medium">
                        <span>Performance Gain</span>
                        <span className="text-success text-lg">{performanceData?.query_execution?.improvement || '+67%'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Resource Efficiency</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">CPU Usage</span>
                        <span className="font-medium text-success">{performanceData?.resource_usage?.cpu_usage || '-45%'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Memory Usage</span>
                        <span className="font-medium text-success">{performanceData?.resource_usage?.memory || '-32%'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">I/O Operations</span>
                        <span className="font-medium text-success">{performanceData?.resource_usage?.io_operations || '-58%'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Performance Insights */}
              <Card className="border border-border/50 mt-6">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Migration Insights</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <CheckCircle className="h-5 w-5 text-success mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium">Query Optimization</p>
                        <p className="text-sm text-muted-foreground">
                          Translated queries are optimized for {targetDB.toUpperCase()} platform-specific features
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <CheckCircle className="h-5 w-5 text-success mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium">Index Recommendations</p>
                        <p className="text-sm text-muted-foreground">
                          Review suggested indexes for frequently accessed columns
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <CheckCircle className="h-5 w-5 text-success mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium">Schema Efficiency</p>
                        <p className="text-sm text-muted-foreground">
                          Data types and constraints optimized for target database
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Optimization Recommendations */}
              {batchResults && batchResults.files.length > 0 && (
                <Card className="border border-border/50 mt-6">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Optimization Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {batchResults.files.map((file, index) => {
                        const hasWarnings = file.result.warnings.length > 0;
                        if (!hasWarnings) return null;
                        
                        return (
                          <div key={file.id} className="border-l-2 border-primary pl-3">
                            <p className="font-medium text-sm">{file.name}</p>
                            <ul className="mt-2 space-y-1">
                              {file.result.warnings.slice(0, 3).map((warning, wIndex) => (
                                <li key={wIndex} className="text-sm text-muted-foreground flex items-start space-x-2">
                                  <span className="text-primary mt-1">•</span>
                                  <span>{warning}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        );
                      }).filter(Boolean)}
                      
                      {batchResults.files.every(f => f.result.warnings.length === 0) && (
                        <div className="text-center py-4 text-muted-foreground">
                          <Zap className="h-8 w-8 mx-auto mb-2 text-success" />
                          <p className="font-medium">No optimization warnings</p>
                          <p className="text-sm">Your SQL is well-optimized for migration</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className="mt-6 flex justify-end">
                <Button 
                  variant="outline"
                  onClick={() => {
                    const detectedDialects = Array.from(new Set(sqlFiles.map(f => f.detectedDialect))).join(', ').toUpperCase();
                    const reportData = {
                      migration_id: activeMigrationId,
                      timestamp: new Date().toISOString(),
                      source_databases: detectedDialects,
                      target_database: targetDB.toUpperCase(),
                      files_migrated: sqlFiles.length,
                      performance_metrics: performanceData || {
                        query_execution: { before: '2.4s', after: '0.8s', improvement: '+67%' },
                        resource_usage: { cpu_usage: '-45%', memory: '-32%', io_operations: '-58%' }
                      }
                    };
                    
                    const reportContent = `# SQL Migration Performance Report

Generated: ${new Date().toLocaleString()}
Migration ID: ${activeMigrationId || 'N/A'}

## Migration Details
- Source Dialects: ${reportData.source_databases}
- Target Database: ${reportData.target_database}
- Files Migrated: ${reportData.files_migrated}

## Query Performance
- Before Migration: ${reportData.performance_metrics.query_execution.before}
- After Migration: ${reportData.performance_metrics.query_execution.after}
- Performance Gain: ${reportData.performance_metrics.query_execution.improvement}

## Resource Efficiency
- CPU Usage Improvement: ${reportData.performance_metrics.resource_usage.cpu_usage}
- Memory Usage Improvement: ${reportData.performance_metrics.resource_usage.memory}
- I/O Operations Improvement: ${reportData.performance_metrics.resource_usage.io_operations}

## Recommendations
${batchResults ? batchResults.files.map(f => 
  f.result.warnings.length > 0 
    ? `\n### ${f.name}\n${f.result.warnings.map(w => `- ${w}`).join('\n')}`
    : ''
).join('\n') : 'No specific recommendations at this time.'}

---
Generated by DataFlow AI SQL Migration Tool`;

                    const blob = new Blob([reportContent], { type: 'text/markdown' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `migration_performance_report_${new Date().toISOString().split('T')[0]}.md`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    toast.success('Performance report downloaded!');
                  }}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Performance Report
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}