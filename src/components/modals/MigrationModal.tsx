import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  GitBranch, 
  Database, 
  ArrowRight, 
  CheckCircle, 
  AlertTriangle,
  Loader2,
  Settings,
  TestTube,
  Play
} from "lucide-react";
import { useStartMigration } from "@/hooks/useApi";

interface MigrationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const databases = [
  { id: "mysql", name: "MySQL", version: "8.0", icon: "🐬", port: 3306 },
  { id: "postgresql", name: "PostgreSQL", version: "14", icon: "🐘", port: 5432 },
  { id: "oracle", name: "Oracle", version: "19c", icon: "🏛️", port: 1521 },
  { id: "mssql", name: "SQL Server", version: "2019", icon: "🏢", port: 1433 },
  { id: "snowflake", name: "Snowflake", version: "Latest", icon: "❄️", port: 443 },
  { id: "redshift", name: "Redshift", version: "Latest", icon: "🚀", port: 5439 }
];

export default function MigrationModal({ open, onOpenChange }: MigrationModalProps) {
  const [activeTab, setActiveTab] = useState("source");
  const [migrationConfig, setMigrationConfig] = useState({
    source: {
      type: "",
      host: "",
      port: "",
      database: "",
      username: "",
      password: "",
      ssl: false
    },
    target: {
      type: "",
      host: "",
      port: "",
      database: "",
      username: "",
      password: "",
      ssl: false
    },
    options: {
      migrateSchema: true,
      migrateData: true,
      preserveConstraints: true,
      optimizeForTarget: true,
      batchSize: 10000,
      parallelWorkers: 4
    }
  });
  const [testResults, setTestResults] = useState<{[key: string]: 'pending' | 'success' | 'error'}>({});
  
  const startMigrationMutation = useStartMigration();

  const updateSourceConfig = (field: string, value: any) => {
    setMigrationConfig(prev => ({
      ...prev,
      source: { ...prev.source, [field]: value }
    }));
  };

  const updateTargetConfig = (field: string, value: any) => {
    setMigrationConfig(prev => ({
      ...prev,
      target: { ...prev.target, [field]: value }
    }));
  };

  const updateOptions = (field: string, value: any) => {
    setMigrationConfig(prev => ({
      ...prev,
      options: { ...prev.options, [field]: value }
    }));
  };

  const testConnection = async (type: 'source' | 'target') => {
    const config = migrationConfig[type];
    
    if (!config.type || !config.host || !config.database) {
      toast.error('Please fill in all required connection fields');
      return;
    }

    setTestResults(prev => ({ ...prev, [type]: 'pending' }));
    
    try {
      // Simulate connection test
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Random success/failure for demo
      const success = Math.random() > 0.2; // 80% success rate
      
      if (success) {
        setTestResults(prev => ({ ...prev, [type]: 'success' }));
        toast.success(`${type === 'source' ? 'Source' : 'Target'} connection successful!`);
      } else {
        setTestResults(prev => ({ ...prev, [type]: 'error' }));
        toast.error(`${type === 'source' ? 'Source' : 'Target'} connection failed. Please check your credentials.`);
      }
    } catch (error) {
      setTestResults(prev => ({ ...prev, [type]: 'error' }));
      toast.error('Connection test failed');
    }
  };

  const startMigration = async () => {
    // Validate configuration
    if (!migrationConfig.source.type || !migrationConfig.target.type) {
      toast.error('Please configure both source and target databases');
      return;
    }

    if (testResults.source !== 'success' || testResults.target !== 'success') {
      toast.error('Please test and verify both database connections before starting migration');
      return;
    }

    try {
      const result = await startMigrationMutation.mutateAsync(migrationConfig);
      
      if (result.data) {
        toast.success('Migration started successfully!', {
          description: `Migration ID: ${result.data.migration_id}`
        });
        
        onOpenChange(false);
        
        // Navigate to SQL migration page to monitor progress
        setTimeout(() => {
          window.location.hash = '#/sql-migration';
        }, 1000);
      }
    } catch (error) {
      toast.error('Failed to start migration');
    }
  };

  const handleDatabaseTypeChange = (type: 'source' | 'target', dbType: string) => {
    const db = databases.find(d => d.id === dbType);
    if (db) {
      if (type === 'source') {
        updateSourceConfig('type', dbType);
        updateSourceConfig('port', db.port.toString());
      } else {
        updateTargetConfig('type', dbType);
        updateTargetConfig('port', db.port.toString());
      }
    }
  };

  const renderConnectionForm = (type: 'source' | 'target') => {
    const config = migrationConfig[type];
    const testResult = testResults[type];
    
    return (
      <div className="space-y-4">
        <div>
          <Label htmlFor={`${type}-type`}>Database Type</Label>
          <Select 
            value={config.type} 
            onValueChange={(value) => handleDatabaseTypeChange(type, value)}
          >
            <SelectTrigger className="mt-1">
              <SelectValue placeholder="Select database type" />
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

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor={`${type}-host`}>Host</Label>
            <Input
              id={`${type}-host`}
              value={config.host}
              onChange={(e) => type === 'source' ? updateSourceConfig('host', e.target.value) : updateTargetConfig('host', e.target.value)}
              placeholder="localhost"
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor={`${type}-port`}>Port</Label>
            <Input
              id={`${type}-port`}
              value={config.port}
              onChange={(e) => type === 'source' ? updateSourceConfig('port', e.target.value) : updateTargetConfig('port', e.target.value)}
              placeholder="5432"
              className="mt-1"
            />
          </div>
        </div>

        <div>
          <Label htmlFor={`${type}-database`}>Database Name</Label>
          <Input
            id={`${type}-database`}
            value={config.database}
            onChange={(e) => type === 'source' ? updateSourceConfig('database', e.target.value) : updateTargetConfig('database', e.target.value)}
            placeholder="my_database"
            className="mt-1"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor={`${type}-username`}>Username</Label>
            <Input
              id={`${type}-username`}
              value={config.username}
              onChange={(e) => type === 'source' ? updateSourceConfig('username', e.target.value) : updateTargetConfig('username', e.target.value)}
              placeholder="username"
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor={`${type}-password`}>Password</Label>
            <Input
              id={`${type}-password`}
              type="password"
              value={config.password}
              onChange={(e) => type === 'source' ? updateSourceConfig('password', e.target.value) : updateTargetConfig('password', e.target.value)}
              placeholder="password"
              className="mt-1"
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id={`${type}-ssl`}
            checked={config.ssl}
            onCheckedChange={(checked) => type === 'source' ? updateSourceConfig('ssl', !!checked) : updateTargetConfig('ssl', !!checked)}
          />
          <Label htmlFor={`${type}-ssl`} className="text-sm">
            Use SSL connection
          </Label>
        </div>

        <div className="flex items-center justify-between pt-4 border-t">
          <div className="flex items-center space-x-2">
            {testResult === 'success' && (
              <>
                <CheckCircle className="h-4 w-4 text-success" />
                <span className="text-sm text-success">Connection verified</span>
              </>
            )}
            {testResult === 'error' && (
              <>
                <AlertTriangle className="h-4 w-4 text-destructive" />
                <span className="text-sm text-destructive">Connection failed</span>
              </>
            )}
          </div>
          <Button
            variant="outline"
            onClick={() => testConnection(type)}
            disabled={testResult === 'pending'}
          >
            {testResult === 'pending' ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <TestTube className="h-4 w-4 mr-2" />
                Test Connection
              </>
            )}
          </Button>
        </div>
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <GitBranch className="h-5 w-5 mr-2" />
            Setup Database Migration
          </DialogTitle>
          <DialogDescription>
            Configure source and target databases for your migration
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="source">Source Database</TabsTrigger>
            <TabsTrigger value="target">Target Database</TabsTrigger>
            <TabsTrigger value="options">Migration Options</TabsTrigger>
            <TabsTrigger value="review">Review & Start</TabsTrigger>
          </TabsList>

          <TabsContent value="source" className="space-y-4">
            <div className="flex items-center space-x-2 mb-4">
              <Database className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-medium">Source Database Configuration</h3>
            </div>
            {renderConnectionForm('source')}
          </TabsContent>

          <TabsContent value="target" className="space-y-4">
            <div className="flex items-center space-x-2 mb-4">
              <Database className="h-5 w-5 text-success" />
              <h3 className="text-lg font-medium">Target Database Configuration</h3>
            </div>
            {renderConnectionForm('target')}
          </TabsContent>

          <TabsContent value="options" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium flex items-center">
                  <Settings className="h-4 w-4 mr-2" />
                  Migration Options
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="migrateSchema"
                      checked={migrationConfig.options.migrateSchema}
                      onCheckedChange={(checked) => updateOptions('migrateSchema', !!checked)}
                    />
                    <Label htmlFor="migrateSchema" className="text-sm">
                      Migrate schema structure
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="migrateData"
                      checked={migrationConfig.options.migrateData}
                      onCheckedChange={(checked) => updateOptions('migrateData', !!checked)}
                    />
                    <Label htmlFor="migrateData" className="text-sm">
                      Migrate data content
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="preserveConstraints"
                      checked={migrationConfig.options.preserveConstraints}
                      onCheckedChange={(checked) => updateOptions('preserveConstraints', !!checked)}
                    />
                    <Label htmlFor="preserveConstraints" className="text-sm">
                      Preserve constraints and indexes
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="optimizeForTarget"
                      checked={migrationConfig.options.optimizeForTarget}
                      onCheckedChange={(checked) => updateOptions('optimizeForTarget', !!checked)}
                    />
                    <Label htmlFor="optimizeForTarget" className="text-sm">
                      Optimize for target platform
                    </Label>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Performance Settings</h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="batchSize" className="text-sm">Batch Size</Label>
                    <Select 
                      value={migrationConfig.options.batchSize.toString()} 
                      onValueChange={(value) => updateOptions('batchSize', parseInt(value))}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1000">1,000 rows</SelectItem>
                        <SelectItem value="10000">10,000 rows</SelectItem>
                        <SelectItem value="50000">50,000 rows</SelectItem>
                        <SelectItem value="100000">100,000 rows</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="parallelWorkers" className="text-sm">Parallel Workers</Label>
                    <Select 
                      value={migrationConfig.options.parallelWorkers.toString()} 
                      onValueChange={(value) => updateOptions('parallelWorkers', parseInt(value))}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 worker</SelectItem>
                        <SelectItem value="2">2 workers</SelectItem>
                        <SelectItem value="4">4 workers</SelectItem>
                        <SelectItem value="8">8 workers</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="review" className="space-y-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Migration Summary</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                {/* Source */}
                <div className="text-center">
                  <div className="p-4 border rounded-lg">
                    <Database className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <h4 className="font-medium">Source</h4>
                    <p className="text-sm text-muted-foreground">
                      {migrationConfig.source.type ? 
                        databases.find(db => db.id === migrationConfig.source.type)?.name : 
                        'Not configured'
                      }
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {migrationConfig.source.host}:{migrationConfig.source.port}
                    </p>
                    <Badge 
                      variant={testResults.source === 'success' ? 'default' : 'destructive'} 
                      className="mt-2"
                    >
                      {testResults.source === 'success' ? 'Connected' : 'Not tested'}
                    </Badge>
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex justify-center">
                  <ArrowRight className="h-8 w-8 text-muted-foreground" />
                </div>

                {/* Target */}
                <div className="text-center">
                  <div className="p-4 border rounded-lg">
                    <Database className="h-8 w-8 mx-auto mb-2 text-success" />
                    <h4 className="font-medium">Target</h4>
                    <p className="text-sm text-muted-foreground">
                      {migrationConfig.target.type ? 
                        databases.find(db => db.id === migrationConfig.target.type)?.name : 
                        'Not configured'
                      }
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {migrationConfig.target.host}:{migrationConfig.target.port}
                    </p>
                    <Badge 
                      variant={testResults.target === 'success' ? 'default' : 'destructive'} 
                      className="mt-2"
                    >
                      {testResults.target === 'success' ? 'Connected' : 'Not tested'}
                    </Badge>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-muted/50 rounded-lg">
                <h4 className="font-medium mb-2">Migration Options</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-success" />
                    <span>Schema: {migrationConfig.options.migrateSchema ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-success" />
                    <span>Data: {migrationConfig.options.migrateData ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-success" />
                    <span>Batch Size: {migrationConfig.options.batchSize.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-success" />
                    <span>Workers: {migrationConfig.options.parallelWorkers}</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <Button
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={startMigration}
                  disabled={
                    startMigrationMutation.isPending ||
                    testResults.source !== 'success' ||
                    testResults.target !== 'success'
                  }
                  className="min-w-[140px]"
                >
                  {startMigrationMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Start Migration
                    </>
                  )}
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}