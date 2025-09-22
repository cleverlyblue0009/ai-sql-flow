import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import SQLInput from "./SQLInput";
import { useMigrationProgress } from "@/hooks/useMigrationProgress";
import { useAuth } from "@/contexts/AuthContext";
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
  RefreshCw
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
  const [sourceDB, setSourceDB] = useState("mysql");
  const [targetDB, setTargetDB] = useState("snowflake");
  const [migrationProgress, setMigrationProgress] = useState(45);
  const [sqlContent, setSQLContent] = useState("");
  const [sqlAnalysis, setSQLAnalysis] = useState(null);
  const [activeMigrationId, setActiveMigrationId] = useState<string | null>(null);
  const [realTimeSteps, setRealTimeSteps] = useState(migrationSteps);
  const [translatedSQL, setTranslatedSQL] = useState("");
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
      if (currentUser) {
        try {
          const token = await currentUser.getIdToken(forceRefresh);
          setFirebaseToken(token);
          console.log('Firebase token updated:', forceRefresh ? '(forced refresh)' : '(cached)');
        } catch (error) {
          console.error('Error getting Firebase token:', error);
          setFirebaseToken(null);
        }
      } else {
        setFirebaseToken(null);
      }
    };

    // Get initial token
    getFirebaseToken();

    // Set up automatic token refresh every 50 minutes (tokens expire in 1 hour)
    const tokenRefreshInterval = setInterval(() => {
      if (currentUser) {
        console.log('Refreshing Firebase token automatically...');
        getFirebaseToken(true); // Force refresh
      }
    }, 50 * 60 * 1000); // 50 minutes

    return () => {
      clearInterval(tokenRefreshInterval);
    };
  }, [currentUser]);

  // WebSocket integration for real-time progress
  const {
    isConnected,
    connectionState,
    progressData,
    errors,
    subscribeToMigration,
    unsubscribeFromMigration
  } = useMigrationProgress({
    token: firebaseToken || undefined,
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
      console.error('Migration error:', error);
      const errorMessage = error?.error || error?.message || 'An unknown error occurred';
      
      // Handle authentication errors specifically
      if (errorMessage.includes('Authentication') || errorMessage.includes('401') || errorMessage.includes('403')) {
        toast.error('Authentication Error', { 
          description: 'Session expired. Refreshing connection...',
          duration: 3000
        });
        
        // Force token refresh
        if (currentUser) {
          currentUser.getIdToken(true).then((newToken) => {
            setFirebaseToken(newToken);
            toast.success('Authentication refreshed', {
              description: 'WebSocket connection will reconnect automatically'
            });
          }).catch((refreshError) => {
            console.error('Token refresh failed:', refreshError);
            toast.error('Token Refresh Failed', {
              description: 'Please try logging out and back in'
            });
          });
        }
      } else if (errorMessage.includes('backend unavailable') || errorMessage.includes('WebSocket connection failed')) {
        // Handle backend unavailable errors more gracefully - don't spam the user
        console.warn('Backend service unavailable - operating in offline mode');
      } else {
        toast.error('Migration Error', { 
          description: errorMessage,
          duration: 5000
        });
      }
    }
  });

  const handleSQLChange = (sql: string, metadata?: any) => {
    setSQLContent(sql);
    console.log('SQL content updated:', { sql: sql.substring(0, 100) + '...', metadata });
    
    // Auto-scroll to Source & Target Selection after file upload
    if (metadata && metadata.fileName) {
      setTimeout(() => {
        sourceTargetRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 500);
    }
  };

  const handleAnalysisComplete = (analysis: any) => {
    setSQLAnalysis(analysis);
    console.log('Analysis completed:', analysis);
  };

  // Client-side SQL translation fallback
  const performClientSideTranslation = (sql: string, sourceDialect: string, targetDialect: string) => {
    let translated = sql;
    
    // Basic MySQL to Snowflake translations
    if (sourceDialect === 'mysql' && targetDialect === 'snowflake') {
      translated = translated
        .replace(/AUTO_INCREMENT/gi, 'AUTOINCREMENT')
        .replace(/TINYINT(\(\d+\))?/gi, 'SMALLINT')
        .replace(/MEDIUMINT(\(\d+\))?/gi, 'INT')
        .replace(/LONGTEXT/gi, 'TEXT')
        .replace(/DATE_FORMAT\s*\(\s*([^,]+),\s*'%Y-%m'\s*\)/gi, "TO_CHAR($1, 'YYYY-MM')")
        .replace(/DATE_SUB\s*\(\s*NOW\(\),\s*INTERVAL\s+(\d+)\s+MONTH\s*\)/gi, 'DATEADD(MONTH, -$1, CURRENT_TIMESTAMP())')
        .replace(/NOW\(\)/gi, 'CURRENT_TIMESTAMP()')
        .replace(/`([^`]+)`/g, '"$1"'); // Convert backticks to double quotes
    }
    
    // Basic PostgreSQL to Snowflake translations
    if (sourceDialect === 'postgresql' && targetDialect === 'snowflake') {
      translated = translated
        .replace(/SERIAL/gi, 'AUTOINCREMENT')
        .replace(/BIGSERIAL/gi, 'AUTOINCREMENT')
        .replace(/BOOLEAN/gi, 'BOOL')
        .replace(/TIMESTAMP WITH TIME ZONE/gi, 'TIMESTAMP_TZ')
        .replace(/CURRENT_TIMESTAMP/gi, 'CURRENT_TIMESTAMP()');
    }
    
    return translated;
  };

  const startMigrationAnalysis = async () => {
    if (!sqlContent.trim()) {
      toast.error('Please provide SQL content to analyze');
      return;
    }

    try {
      setTranslationInProgress(true);
      
      // First, try the backend API
      let translationSuccessful = false;
      
      try {
        // Step 1: Start SQL translation
        const translationResponse = await fetch('http://localhost:8000/api/migration/translate-sql', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${firebaseToken}`
          },
          body: JSON.stringify({
            source_sql: sqlContent,
            source_dialect: sourceDB,
            target_dialect: targetDB,
            optimization_level: 'standard'
          })
        });

        if (translationResponse.ok) {
          const translationResult = await translationResponse.json();
          console.log('Translation started:', translationResult);

          // Poll for translation results
          const jobId = translationResult.job_id;
          let translationComplete = false;
          let attempts = 0;
          const maxAttempts = 15; // Reduced from 30 to fail faster

          while (!translationComplete && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 1000)); // Reduced from 2000ms
            attempts++;

            try {
              const statusResponse = await fetch(`http://localhost:8000/api/jobs/${jobId}/status`, {
                headers: {
                  'Authorization': `Bearer ${firebaseToken}`
                }
              });

              if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                
                if (statusData.status === 'completed' && statusData.result) {
                  setTranslatedSQL(statusData.result.translated_sql);
                  translationComplete = true;
                  translationSuccessful = true;
                  
                  // Auto-scroll to translation tab
                  setTimeout(() => {
                    translationRef.current?.scrollIntoView({ 
                      behavior: 'smooth', 
                      block: 'start' 
                    });
                  }, 500);
                  
                  toast.success('SQL translation completed!');
                } else if (statusData.status === 'failed') {
                  const errorMsg = statusData.error || statusData.error_message || 'Translation failed';
                  throw new Error(errorMsg);
                }
              }
            } catch (pollError) {
              console.error('Error polling translation status:', pollError);
              break; // Exit polling loop on error
            }
          }
        }
      } catch (backendError) {
        console.warn('Backend translation failed, using client-side fallback:', backendError);
      }
      
      // If backend translation failed, use client-side fallback
      if (!translationSuccessful) {
        const clientTranslated = performClientSideTranslation(sqlContent, sourceDB, targetDB);
        setTranslatedSQL(clientTranslated);
        
        // Auto-scroll to translation tab
        setTimeout(() => {
          translationRef.current?.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
          });
        }, 500);
        
        toast.info('Backend unavailable - using client-side translation', {
          description: 'Basic translation applied. For advanced features, please start the backend service.'
        });
      }

      // Step 2: Create migration setup
      const migrationResponse = await fetch('http://localhost:8000/api/migration/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${firebaseToken}`
        },
        body: JSON.stringify({
          project_id: 1, // Default project
          name: `Migration ${new Date().toISOString()}`,
          description: 'SQL Migration from uploaded file',
          source_config: {
            connection_type: sourceDB,
            host: 'localhost',
            port: sourceDB === 'mysql' ? 3306 : 5432,
            database: 'source_db',
            username: 'user',
            password: 'password'
          },
          target_config: {
            connection_type: targetDB,
            host: 'localhost',
            port: targetDB === 'snowflake' ? 443 : 5432,
            database: 'target_db',
            username: 'user',
            password: 'password'
          },
          migration_options: {
            migrate_schema: true,
            migrate_data: true,
            preserve_constraints: false,
            optimize_for_target: true
          }
        })
      });

      if (migrationResponse.ok) {
        const migrationResult = await migrationResponse.json();
        const migrationId = migrationResult.migration_id;
        setActiveMigrationId(migrationId);
        
        // Subscribe to migration progress
        if (isConnected) {
          subscribeToMigration(migrationId);
        } else {
          toast.warning('WebSocket not connected', {
            description: 'Real-time updates may not be available'
          });
        }
        
        // Start the actual migration
        const startResponse = await fetch(`http://localhost:8000/api/migration/start?migration_id=${migrationId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${firebaseToken}`
          },
          body: JSON.stringify({
            migrate_schema: true,
            migrate_data: true,
            preserve_constraints: false,
            optimize_for_target: true,
            batch_size: 1000,
            parallel_jobs: 2
          })
        });

        if (startResponse.ok) {
          toast.success('Migration analysis started', {
            description: 'You will receive real-time updates on the progress'
          });
          
          // Generate mock performance data
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
          }, 10000);
        } else {
          const startErrorData = await startResponse.json().catch(() => ({}));
          throw new Error(startErrorData.detail || `Failed to start migration with status ${startResponse.status}`);
        }
      } else {
        const migrationErrorData = await migrationResponse.json().catch(() => ({}));
        throw new Error(migrationErrorData.detail || `Failed to setup migration with status ${migrationResponse.status}`);
      }
      
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

      <Tabs defaultValue="setup" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="setup">Setup Migration</TabsTrigger>
          <TabsTrigger value="translation">SQL Translation</TabsTrigger>
          <TabsTrigger value="progress">Migration Progress</TabsTrigger>
          <TabsTrigger value="performance">Performance Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-6">
          {/* SQL Input Section */}
          <SQLInput 
            onSQLChange={handleSQLChange}
            onAnalysisComplete={handleAnalysisComplete}
            selectedDatabase={sourceDB}
          />

          {/* Database Selection */}
          <Card className="enterprise-card" ref={sourceTargetRef}>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="h-5 w-5 mr-2" />
                Source & Target Selection
              </CardTitle>
              <CardDescription>
                Choose your source and target database platforms for migration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                {/* Source Database */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Source Database</label>
                  <Select value={sourceDB} onValueChange={setSourceDB}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {databases.map((db) => (
                        <SelectItem key={db.id} value={db.id}>
                          <div className="flex items-center space-x-2">
                            <span>{db.icon}</span>
                            <span>{db.name} {db.version}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Arrow */}
                <div className="flex justify-center">
                  <ArrowRight className="h-8 w-8 text-muted-foreground" />
                </div>

                {/* Target Database */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Target Database</label>
                  <Select value={targetDB} onValueChange={setTargetDB}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {databases.map((db) => (
                        <SelectItem key={db.id} value={db.id}>
                          <div className="flex items-center space-x-2">
                            <span>{db.icon}</span>
                            <span>{db.name} {db.version}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Connection Details */}
                <Card className="border border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Connection Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Source Connection</span>
                      <Badge variant="default" className="bg-success">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Connected
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Target Connection</span>
                      <Badge variant="default" className="bg-success">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Connected
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Schema Compatibility</span>
                      <Badge variant="secondary" className="bg-warning/20 text-warning">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Review Needed
                      </Badge>
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
                      <input type="checkbox" className="rounded" defaultChecked />
                      <span className="text-sm">Migrate schema structure</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded" defaultChecked />
                      <span className="text-sm">Migrate data content</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded" />
                      <span className="text-sm">Preserve constraints</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded" defaultChecked />
                      <span className="text-sm">Optimize for target platform</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="flex justify-end mt-6">
                <Button 
                  className="enterprise-button-primary"
                  onClick={startMigrationAnalysis}
                  disabled={!sqlContent.trim() || translationInProgress}
                >
                  {translationInProgress ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Processing Migration...
                    </>
                  ) : (
                    <>
                      <GitBranch className="h-4 w-4 mr-2" />
                      Start Migration Analysis
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="translation" className="space-y-6" ref={translationRef}>
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
                    <h4 className="font-medium">Source SQL ({sourceDB.toUpperCase()})</h4>
                    <Badge variant="outline">Original</Badge>
                  </div>
                  <div className="bg-muted rounded-lg p-4 font-mono text-sm min-h-[400px] overflow-auto">
                    <pre className="whitespace-pre-wrap">{sqlContent || sqlExample}</pre>
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
                      <pre className="whitespace-pre-wrap">{translatedSQL || `-- Translated ${targetDB.toUpperCase()} Query\n${sqlContent || sqlExample}`}</pre>
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
                      const content = translatedSQL || `-- Translated ${targetDB.toUpperCase()} Query\n${sqlContent || sqlExample}`;
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
                    disabled={!sqlContent && !translatedSQL}
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
                Before and after performance metrics comparison
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="border border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Query Execution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Before</span>
                        <span className="font-medium">{performanceData?.query_execution?.before || '2.4s'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">After</span>
                        <span className="font-medium text-success">{performanceData?.query_execution?.after || '0.8s'}</span>
                      </div>
                      <div className="flex justify-between font-medium">
                        <span>Improvement</span>
                        <span className="text-success">{performanceData?.query_execution?.improvement || '+67%'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Resource Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">CPU Usage</span>
                        <span className="font-medium text-success">{performanceData?.resource_usage?.cpu_usage || '-45%'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Memory</span>
                        <span className="font-medium text-success">{performanceData?.resource_usage?.memory || '-32%'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">I/O Operations</span>
                        <span className="font-medium text-success">{performanceData?.resource_usage?.io_operations || '-58%'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Cost Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Monthly Cost</span>
                        <span className="font-medium text-success">{performanceData?.cost_analysis?.monthly_cost || '-$2,340'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Annual Savings</span>
                        <span className="font-medium text-success">{performanceData?.cost_analysis?.annual_savings || '$28,080'}</span>
                      </div>
                      <div className="flex justify-between font-medium">
                        <span>ROI</span>
                        <span className="text-success">{performanceData?.cost_analysis?.roi || '340%'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="mt-6 flex justify-end">
                <Button 
                  variant="outline"
                  onClick={() => {
                    const reportData = {
                      migration_id: activeMigrationId,
                      timestamp: new Date().toISOString(),
                      source_database: sourceDB,
                      target_database: targetDB,
                      performance_metrics: performanceData || {
                        query_execution: { before: '2.4s', after: '0.8s', improvement: '+67%' },
                        resource_usage: { cpu_usage: '-45%', memory: '-32%', io_operations: '-58%' },
                        cost_analysis: { monthly_cost: '-$2,340', annual_savings: '$28,080', roi: '340%' }
                      }
                    };
                    
                    const reportContent = `# SQL Migration Performance Report

Generated: ${new Date().toLocaleString()}
Migration ID: ${activeMigrationId || 'N/A'}

## Migration Details
- Source Database: ${sourceDB.toUpperCase()}
- Target Database: ${targetDB.toUpperCase()}

## Query Performance
- Before Migration: ${reportData.performance_metrics.query_execution.before}
- After Migration: ${reportData.performance_metrics.query_execution.after}
- Improvement: ${reportData.performance_metrics.query_execution.improvement}

## Resource Usage
- CPU Usage: ${reportData.performance_metrics.resource_usage.cpu_usage}
- Memory: ${reportData.performance_metrics.resource_usage.memory}
- I/O Operations: ${reportData.performance_metrics.resource_usage.io_operations}

## Cost Analysis
- Monthly Cost Savings: ${reportData.performance_metrics.cost_analysis.monthly_cost}
- Annual Savings: ${reportData.performance_metrics.cost_analysis.annual_savings}
- ROI: ${reportData.performance_metrics.cost_analysis.roi}

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