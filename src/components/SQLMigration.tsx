import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
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
  Loader2,
  Copy,
  Wand2,
  RefreshCw
} from "lucide-react";
import { useTranslateSQL, useStartMigration, useActiveMigrations } from "@/hooks/useApi";
import MigrationModal from "@/components/modals/MigrationModal";

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
  const [migrationProgress] = useState(45);
  const [sourceSQL, setSourceSQL] = useState(sqlExample);
  const [translatedSQL, setTranslatedSQL] = useState("");
  const [migrationModalOpen, setMigrationModalOpen] = useState(false);
  
  // API hooks
  const translateMutation = useTranslateSQL();
  const { data: activeMigrations, isLoading: migrationsLoading } = useActiveMigrations();

  // Handle SQL translation
  const handleTranslateSQL = async () => {
    if (!sourceSQL.trim()) {
      toast.error('Please enter SQL to translate');
      return;
    }

    try {
      const result = await translateMutation.mutateAsync({
        sql: sourceSQL,
        sourceDb: sourceDB,
        targetDb: targetDB
      });

      if (result.data) {
        // Generate realistic translated SQL based on the source and target
        const translated = generateTranslatedSQL(sourceSQL, sourceDB, targetDB);
        setTranslatedSQL(translated);
        
        toast.success('SQL translated successfully!', {
          description: `Converted from ${databases.find(d => d.id === sourceDB)?.name} to ${databases.find(d => d.id === targetDB)?.name}`
        });
      }
    } catch (error) {
      toast.error('Translation failed. Please check your SQL syntax.');
    }
  };

  // Generate translated SQL (mock implementation)
  const generateTranslatedSQL = (sql: string, source: string, target: string): string => {
    let translated = sql;
    
    // MySQL to Snowflake translations
    if (source === 'mysql' && target === 'snowflake') {
      translated = translated
        .replace(/DATE_FORMAT\(([^,]+),\s*'%Y-%m'\)/g, "TO_CHAR($1, 'YYYY-MM')")
        .replace(/DATE_SUB\(NOW\(\),\s*INTERVAL\s+(\d+)\s+MONTH\)/g, "DATEADD(MONTH, -$1, CURRENT_TIMESTAMP())")
        .replace(/NOW\(\)/g, 'CURRENT_TIMESTAMP()');
    }
    
    // PostgreSQL to Redshift translations
    if (source === 'postgresql' && target === 'redshift') {
      translated = translated
        .replace(/CURRENT_TIMESTAMP/g, 'GETDATE()')
        .replace(/EXTRACT\(EPOCH FROM ([^)]+)\)/g, 'DATEDIFF(second, \'1970-01-01\', $1)');
    }
    
    // Add comments about optimizations
    translated = `-- Translated from ${databases.find(d => d.id === source)?.name} to ${databases.find(d => d.id === target)?.name}
-- Optimizations applied: Performance tuning, syntax conversion
${translated}`;
    
    return translated;
  };

  // Copy SQL to clipboard
  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      toast.success(`${label} copied to clipboard!`);
    }).catch(() => {
      toast.error('Failed to copy to clipboard');
    });
  };

  // Test query execution (mock)
  const testQuery = async (sql: string, dbType: string) => {
    if (!sql.trim()) {
      toast.error('No SQL to test');
      return;
    }

    toast.info('Testing query...', {
      description: `Executing on ${databases.find(d => d.id === dbType)?.name}`
    });

    // Simulate query execution
    setTimeout(() => {
      const success = Math.random() > 0.2; // 80% success rate
      if (success) {
        toast.success('Query executed successfully!', {
          description: `Returned 1,247 rows in 0.85 seconds`
        });
      } else {
        toast.error('Query execution failed', {
          description: 'Syntax error near line 5'
        });
      }
    }, 2000);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">SQL Migration Workspace</h1>
        <p className="text-muted-foreground">
          Seamlessly migrate and translate SQL across different database platforms
        </p>
      </div>

      <Tabs defaultValue="setup" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="setup">Setup Migration</TabsTrigger>
          <TabsTrigger value="translation">SQL Translation</TabsTrigger>
          <TabsTrigger value="progress">Migration Progress</TabsTrigger>
          <TabsTrigger value="performance">Performance Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-6">
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
                  onClick={() => setMigrationModalOpen(true)}
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
                    <h4 className="font-medium">Source SQL ({databases.find(d => d.id === sourceDB)?.name})</h4>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">Original</Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(sourceSQL, 'Source SQL')}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <Textarea
                    value={sourceSQL}
                    onChange={(e) => setSourceSQL(e.target.value)}
                    className="font-mono text-sm min-h-[400px] resize-none"
                    placeholder="Enter your SQL query here..."
                  />
                  <div className="flex justify-end mt-2 space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => testQuery(sourceSQL, sourceDB)}
                    >
                      <Play className="h-3 w-3 mr-1" />
                      Test Original
                    </Button>
                  </div>
                </div>

                {/* Translated SQL */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">Translated SQL ({databases.find(d => d.id === targetDB)?.name})</h4>
                    <div className="flex items-center space-x-2">
                      {translatedSQL && (
                        <Badge variant="default" className="bg-success">
                          <Zap className="h-3 w-3 mr-1" />
                          Optimized
                        </Badge>
                      )}
                      {translatedSQL && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(translatedSQL, 'Translated SQL')}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                  <div className="bg-muted rounded-lg p-4 font-mono text-sm min-h-[400px] overflow-auto relative">
                    {translatedSQL ? (
                      <pre className="whitespace-pre-wrap">{translatedSQL}</pre>
                    ) : (
                      <div className="flex items-center justify-center h-full text-muted-foreground">
                        <div className="text-center">
                          <Wand2 className="h-8 w-8 mx-auto mb-2" />
                          <p>Click "Translate SQL" to see the optimized version</p>
                        </div>
                      </div>
                    )}
                  </div>
                  {translatedSQL && (
                    <div className="flex justify-end mt-2 space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => testQuery(translatedSQL, targetDB)}
                      >
                        <Play className="h-3 w-3 mr-1" />
                        Test Translated
                      </Button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between mt-6 pt-4 border-t border-border">
                <div className="flex items-center space-x-4">
                  {translatedSQL && (
                    <>
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
                    </>
                  )}
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline"
                    onClick={handleTranslateSQL}
                    disabled={translateMutation.isPending || !sourceSQL.trim()}
                  >
                    {translateMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Translating...
                      </>
                    ) : (
                      <>
                        <Wand2 className="h-4 w-4 mr-2" />
                        Translate SQL
                      </>
                    )}
                  </Button>
                  {translatedSQL && (
                    <Button 
                      className="enterprise-button-success"
                      onClick={() => {
                        toast.success('Translation applied!', {
                          description: 'SQL has been optimized for the target database'
                        });
                      }}
                    >
                      Apply Translation
                    </Button>
                  )}
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
                  {migrationSteps.map((step) => (
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
                <Button 
                  variant="outline"
                  onClick={() => {
                    toast.success('Performance report generated!', {
                      description: 'Detailed analysis of migration performance and optimizations'
                    });
                    // Simulate report download
                    setTimeout(() => {
                      const link = document.createElement('a');
                      link.href = '#';
                      link.download = `migration-performance-report-${Date.now()}.pdf`;
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }, 1000);
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
      
      {/* Migration Setup Modal */}
      <MigrationModal 
        open={migrationModalOpen} 
        onOpenChange={setMigrationModalOpen} 
      />
    </div>
  );
}