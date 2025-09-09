import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { 
  TrendingUp, 
  Database, 
  CheckCircle, 
  Clock, 
  AlertTriangle,
  FileText,
  Upload,
  GitBranch,
  DollarSign,
  Users,
  ArrowUpRight
} from "lucide-react";
import heroImage from "@/assets/hero-data-center.jpg";

const metrics = [
  {
    title: "Data Quality Score",
    value: "94.2%",
    change: "+2.4%",
    trend: "up",
    icon: CheckCircle,
    color: "text-success"
  },
  {
    title: "Active Migrations",
    value: "12",
    change: "+3",
    trend: "up", 
    icon: GitBranch,
    color: "text-primary"
  },
  {
    title: "Success Rate",
    value: "99.1%",
    change: "+0.5%",
    trend: "up",
    icon: TrendingUp,
    color: "text-success"
  },
  {
    title: "Cost Savings",
    value: "$2.4M",
    change: "+$340K",
    trend: "up",
    icon: DollarSign,
    color: "text-success"
  }
];

const recentActivities = [
  {
    id: 1,
    type: "migration",
    title: "PostgreSQL to Snowflake migration completed",
    timestamp: "2 minutes ago",
    status: "success"
  },
  {
    id: 2,
    type: "quality",
    title: "Data quality check started for customer_data table",
    timestamp: "15 minutes ago", 
    status: "running"
  },
  {
    id: 3,
    type: "alert",
    title: "Schema validation warning in orders table",
    timestamp: "1 hour ago",
    status: "warning"
  },
  {
    id: 4,
    type: "migration",
    title: "MySQL migration queued for processing",
    timestamp: "2 hours ago",
    status: "pending"
  }
];

const quickActions = [
  {
    title: "Start New Migration",
    description: "Migrate data between databases",
    icon: GitBranch,
    action: "migration",
    color: "bg-primary hover:bg-primary/90"
  },
  {
    title: "Upload Data",
    description: "Upload files for quality analysis", 
    icon: Upload,
    action: "upload",
    color: "bg-success hover:bg-success/90"
  },
  {
    title: "Generate Report",
    description: "Create comprehensive analysis report",
    icon: FileText,
    action: "report", 
    color: "bg-enterprise-blue-light hover:bg-enterprise-blue-light/90"
  }
];

export default function Dashboard() {
  const [apiStatus, setApiStatus] = useState<string>("Not tested");
  const [isLoading, setIsLoading] = useState(false);

  const testApiConnection = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/test');
      const data = await response.json();
      setApiStatus(`✅ Connected! ${data.message}`);
    } catch (error) {
      setApiStatus(`❌ Connection failed: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="hero-section relative">
        <div 
          className="absolute inset-0 opacity-20 bg-cover bg-center rounded-lg"
          style={{ backgroundImage: `url(${heroImage})` }}
        />
        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold mb-2">
                AI-Powered Data Platform
              </h1>
              <p className="text-lg opacity-90 mb-6 md:mb-0">
                Streamline your data cleaning and SQL migrations with enterprise-grade AI
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold mb-1">1,247</div>
              <div className="text-sm opacity-80">Tables Processed Today</div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric) => (
          <Card key={metric.title} className="metrics-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    {metric.title}
                  </p>
                  <p className="text-2xl font-bold">{metric.value}</p>
                  <div className="flex items-center mt-2">
                    <ArrowUpRight className="h-4 w-4 text-success mr-1" />
                    <span className="text-sm text-success font-medium">
                      {metric.change}
                    </span>
                  </div>
                </div>
                <div className={`${metric.color}`}>
                  <metric.icon className="h-8 w-8" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity Timeline */}
        <div className="lg:col-span-2">
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Clock className="h-5 w-5 mr-2" />
                Recent Activity
              </CardTitle>
              <CardDescription>
                Latest platform activities and alerts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivities.map((activity) => (
                  <div key={activity.id} className="flex items-start space-x-4 p-3 rounded-lg border border-border/50 hover:bg-muted/30 transition-colors">
                    <div className="flex-shrink-0">
                      {activity.type === 'migration' && (
                        <GitBranch className="h-5 w-5 text-primary mt-0.5" />
                      )}
                      {activity.type === 'quality' && (
                        <CheckCircle className="h-5 w-5 text-success mt-0.5" />
                      )}
                      {activity.type === 'alert' && (
                        <AlertTriangle className="h-5 w-5 text-warning mt-0.5" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground">
                        {activity.title}
                      </p>
                      <div className="flex items-center mt-1 space-x-2">
                        <Badge 
                          variant={
                            activity.status === 'success' ? 'default' :
                            activity.status === 'warning' ? 'secondary' :
                            activity.status === 'running' ? 'outline' : 'secondary'
                          }
                          className="text-xs"
                        >
                          {activity.status}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {activity.timestamp}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>
                Commonly used platform features
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {quickActions.map((action) => (
                <Button
                  key={action.title}
                  className={`w-full justify-start h-auto p-4 ${action.color} text-white`}
                  variant="default"
                >
                  <div className="flex items-center w-full">
                    <action.icon className="h-5 w-5 mr-3 flex-shrink-0" />
                    <div className="text-left">
                      <div className="font-medium">{action.title}</div>
                      <div className="text-sm opacity-90 mt-1">
                        {action.description}
                      </div>
                    </div>
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>

          {/* API Connection Test */}
          <Card className="enterprise-card mt-6">
            <CardHeader>
              <CardTitle>API Connection Test</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button 
                onClick={testApiConnection} 
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? "Testing..." : "Test Backend Connection"}
              </Button>
              <div className="text-sm p-3 bg-muted rounded">
                Status: {apiStatus}
              </div>
            </CardContent>
          </Card>

          {/* System Status */}
          <Card className="enterprise-card mt-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="h-5 w-5 mr-2" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Data Processing</span>
                  <span className="text-success">Operational</span>
                </div>
                <Progress value={98} className="h-2" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Migration Engine</span>
                  <span className="text-success">Operational</span>
                </div>
                <Progress value={94} className="h-2" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>AI Processing</span>
                  <span className="text-success">Operational</span>
                </div>
                <Progress value={96} className="h-2" />
              </div>
              <div className="pt-2 flex items-center text-sm text-muted-foreground">
                <Users className="h-4 w-4 mr-2" />
                <span>247 active users</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}