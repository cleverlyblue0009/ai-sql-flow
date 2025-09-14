import { useState, useEffect } from "react";
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
  WifiOff
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

  // WebSocket integration for real-time progress
  const {
    isConnected,
    connectionState,
    progressData,
    errors,
    subscribeToMigration,
    unsubscribeFromMigration
  } = useMigrationProgress({
    token: localStorage.getItem('token') || undefined,
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
      toast.error('Migration Error', { description: error.error });
    }
  });

  const handleSQLChange = (sql: string, metadata?: any) => {
    setSQLContent(sql);
    console.log('SQL content updated:', { sql: sql.substring(0, 100) + '...', metadata });
  };

  const handleAnalysisComplete = (analysis: any) => {
    setSQLAnalysis(analysis);
    console.log('Analysis completed:', analysis);
  };

  const startMigrationAnalysis = async () => {
    if (!sqlContent.trim()) {
      toast.error('Please provide SQL content to analyze');
      return;
    }

    try {
      // Here you would typically call your API to start the migration
      const migrationId = `migration_${Date.now()}`;
      setActiveMigrationId(migrationId);
      
      // Subscribe to migration progress
      if (isConnected) {
        subscribeToMigration(migrationId);
      }
      
      toast.success('Migration analysis started', {
        description: 'You will receive real-time updates on the progress'
      });
      
    } catch (error) {
      toast.error('Failed to start migration analysis');
      console.error(error);
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
          
          {/* WebSocket Connection Status */}
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Badge variant="default" className="bg-success">
                <Wifi className="h-3 w-3 mr-1" />
                Connected
              </Badge>
            ) : (
              <Badge variant="secondary" className="bg-warning/20 text-warning">
                <WifiOff className="h-3 w-3 mr-1" />
                {connectionState === 'connecting' ? 'Connecting...' : 'Disconnected'}
              </Badge>
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
          <Card className="enterprise-card">
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
                  disabled={!sqlContent.trim() || !isConnected}
                >
                  <GitBranch className="h-4 w-4 mr-2" />
                  Start Migration Analysis
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="translation" className="space-y-6">
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
                    <h4 className="font-medium">Source SQL (MySQL)</h4>
                    <Badge variant="outline">Original</Badge>
                  </div>
                  <div className="bg-muted rounded-lg p-4 font-mono text-sm min-h-[400px] overflow-auto">
                    <pre className="whitespace-pre-wrap">{sqlExample}</pre>
                  </div>
                </div>

                {/* Translated SQL */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">Translated SQL (Snowflake)</h4>
                    <Badge variant="default" className="bg-success">
                      <Zap className="h-3 w-3 mr-1" />
                      Optimized
                    </Badge>
                  </div>
                  <div className="bg-muted rounded-lg p-4 font-mono text-sm min-h-[400px] overflow-auto">
                    <pre className="whitespace-pre-wrap">{translatedSQL}</pre>
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
                        <span className="font-medium">2.4s</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">After</span>
                        <span className="font-medium text-success">0.8s</span>
                      </div>
                      <div className="flex justify-between font-medium">
                        <span>Improvement</span>
                        <span className="text-success">+67%</span>
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
                        <span className="font-medium text-success">-45%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Memory</span>
                        <span className="font-medium text-success">-32%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">I/O Operations</span>
                        <span className="font-medium text-success">-58%</span>
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
                        <span className="font-medium text-success">-$2,340</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Annual Savings</span>
                        <span className="font-medium text-success">$28,080</span>
                      </div>
                      <div className="flex justify-between font-medium">
                        <span>ROI</span>
                        <span className="text-success">340%</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="mt-6 flex justify-end">
                <Button variant="outline">
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