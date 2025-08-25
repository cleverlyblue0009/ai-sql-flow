import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Settings as SettingsIcon, 
  Database, 
  Users, 
  Key, 
  Bell, 
  Shield,
  Zap,
  CheckCircle,
  AlertTriangle,
  Plus,
  Edit,
  Trash2
} from "lucide-react";

const dbConnections = [
  { 
    id: 1, 
    name: "Production MySQL", 
    type: "MySQL", 
    host: "prod-mysql.company.com", 
    status: "connected",
    lastTest: "2 minutes ago"
  },
  { 
    id: 2, 
    name: "Warehouse Snowflake", 
    type: "Snowflake", 
    host: "company.snowflakecomputing.com", 
    status: "connected",
    lastTest: "5 minutes ago"
  },
  { 
    id: 3, 
    name: "Analytics Redshift", 
    type: "Redshift", 
    host: "analytics.redshift.amazonaws.com", 
    status: "error",
    lastTest: "1 hour ago"
  }
];

const teamMembers = [
  { 
    id: 1, 
    name: "Sarah Chen", 
    email: "sarah.chen@company.com", 
    role: "Admin", 
    status: "active",
    lastActive: "Online"
  },
  { 
    id: 2, 
    name: "Michael Rodriguez", 
    email: "m.rodriguez@company.com", 
    role: "Data Engineer", 
    status: "active",
    lastActive: "2 hours ago"
  },
  { 
    id: 3, 
    name: "Lisa Park", 
    email: "lisa.park@company.com", 
    role: "Database Admin", 
    status: "inactive",
    lastActive: "1 week ago"
  }
];

const apiIntegrations = [
  { name: "Slack", description: "Real-time notifications", status: "connected", icon: "💬" },
  { name: "Email (SMTP)", description: "Alert delivery", status: "connected", icon: "📧" },
  { name: "Webhook", description: "Custom integrations", status: "configured", icon: "🔗" },
  { name: "Jira", description: "Issue tracking", status: "disconnected", icon: "📋" }
];

export default function Settings() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Settings & Configuration</h1>
        <p className="text-muted-foreground">
          Manage platform settings, database connections, users, and integrations
        </p>
      </div>

      <Tabs defaultValue="connections" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="connections">Database Connections</TabsTrigger>
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="ai">AI Configuration</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>

        <TabsContent value="connections" className="space-y-6">
          <Card className="enterprise-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center">
                    <Database className="h-5 w-5 mr-2" />
                    Database Connections
                  </CardTitle>
                  <CardDescription>
                    Manage and monitor your database connections for migrations and quality checks
                  </CardDescription>
                </div>
                <Button className="enterprise-button-primary">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Connection
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dbConnections.map((connection) => (
                  <div key={connection.id} className="flex items-center justify-between p-4 rounded-lg border border-border/50 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${
                        connection.status === 'connected' ? 'bg-success' : 'bg-danger'
                      }`} />
                      <div>
                        <p className="font-medium">{connection.name}</p>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <span>{connection.type}</span>
                          <span>•</span>
                          <span>{connection.host}</span>
                          <span>•</span>
                          <span>Last tested: {connection.lastTest}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Badge variant={connection.status === 'connected' ? 'default' : 'destructive'}>
                        {connection.status}
                      </Badge>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        Test Connection
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-6">
          <Card className="enterprise-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center">
                    <Users className="h-5 w-5 mr-2" />
                    Team Management
                  </CardTitle>
                  <CardDescription>
                    Manage user access, roles, and permissions for your team
                  </CardDescription>
                </div>
                <Button className="enterprise-button-primary">
                  <Plus className="h-4 w-4 mr-2" />
                  Invite User
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {teamMembers.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-4 rounded-lg border border-border/50">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-medium">
                        {member.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div>
                        <p className="font-medium">{member.name}</p>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <span>{member.email}</span>
                          <span>•</span>
                          <span>Last active: {member.lastActive}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Badge variant={member.role === 'Admin' ? 'default' : 'secondary'}>
                        {member.role}
                      </Badge>
                      <Badge variant={member.status === 'active' ? 'default' : 'outline'}>
                        {member.status}
                      </Badge>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-muted/30 rounded-lg">
                <h4 className="font-medium mb-3">Role Permissions</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="font-medium mb-2">Admin</p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>• Full platform access</li>
                      <li>• User management</li>
                      <li>• System configuration</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium mb-2">Data Engineer</p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>• Data quality tools</li>
                      <li>• SQL migration</li>
                      <li>• Performance monitoring</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium mb-2">Database Admin</p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>• Database connections</li>
                      <li>• Migration oversight</li>
                      <li>• System monitoring</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai" className="space-y-6">
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="h-5 w-5 mr-2" />
                AI Model Configuration
              </CardTitle>
              <CardDescription>
                Configure AI algorithms and processing parameters for optimal performance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Data Quality Models</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Anomaly Detection</p>
                        <p className="text-xs text-muted-foreground">Advanced outlier identification</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Semantic Validation</p>
                        <p className="text-xs text-muted-foreground">Context-aware data validation</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Pattern Recognition</p>
                        <p className="text-xs text-muted-foreground">Automatic pattern detection</p>
                      </div>
                      <Switch />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">SQL Translation Models</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Syntax Translation</p>
                        <p className="text-xs text-muted-foreground">Cross-platform SQL conversion</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Performance Optimization</p>
                        <p className="text-xs text-muted-foreground">Query performance enhancement</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Semantic Preservation</p>
                        <p className="text-xs text-muted-foreground">Maintain query meaning</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-muted/30 rounded-lg">
                <h4 className="font-medium mb-3">Processing Thresholds</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium">Confidence Threshold</label>
                    <div className="mt-2 flex items-center space-x-2">
                      <span className="text-sm">85%</span>
                      <div className="flex-1 h-2 bg-muted rounded">
                        <div className="h-2 bg-primary rounded" style={{width: '85%'}} />
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Processing Timeout</label>
                    <div className="mt-2 text-sm font-medium">300 seconds</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Batch Size</label>
                    <div className="mt-2 text-sm font-medium">10,000 rows</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations" className="space-y-6">
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Key className="h-5 w-5 mr-2" />
                API Integrations
              </CardTitle>
              <CardDescription>
                Connect external services and configure webhooks for notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {apiIntegrations.map((integration) => (
                  <div key={integration.name} className="flex items-center justify-between p-4 rounded-lg border border-border/50">
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl">{integration.icon}</div>
                      <div>
                        <p className="font-medium">{integration.name}</p>
                        <p className="text-sm text-muted-foreground">{integration.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Badge variant={
                        integration.status === 'connected' ? 'default' :
                        integration.status === 'configured' ? 'secondary' : 'outline'
                      }>
                        {integration.status}
                      </Badge>
                      <Button variant="outline" size="sm">
                        {integration.status === 'disconnected' ? 'Connect' : 'Configure'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="h-5 w-5 mr-2" />
                Security & Compliance
              </CardTitle>
              <CardDescription>
                Security settings, audit logs, and compliance configurations
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Security Settings</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Two-Factor Authentication</p>
                        <p className="text-xs text-muted-foreground">Require 2FA for all users</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">API Rate Limiting</p>
                        <p className="text-xs text-muted-foreground">Prevent API abuse</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Audit Logging</p>
                        <p className="text-xs text-muted-foreground">Log all user actions</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">Compliance</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">GDPR Compliance</span>
                      <CheckCircle className="h-5 w-5 text-success" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">SOC 2 Type II</span>
                      <CheckCircle className="h-5 w-5 text-success" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">HIPAA Compliance</span>
                      <AlertTriangle className="h-5 w-5 text-warning" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-muted/30 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">Security Score</h4>
                  <span className="text-xl font-bold text-success">A+</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  Your platform security configuration meets enterprise-grade standards with 
                  comprehensive encryption, access controls, and audit capabilities.
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}