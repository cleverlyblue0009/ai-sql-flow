import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
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
  ArrowUpRight,
  Loader2,
  AlertCircle,
  RefreshCw
} from "lucide-react";
import { toast } from "sonner";
import heroImage from "@/assets/hero-data-center.jpg";
import { useDashboardOverview, useApiHealth } from "@/hooks/useApi";
import FileUploadModal from "@/components/modals/FileUploadModal";
import MigrationModal from "@/components/modals/MigrationModal";
import ReportModal from "@/components/modals/ReportModal";

// Quick actions configuration - static as these are UI actions
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

// Helper function to format currency
const formatCurrency = (amount: number): string => {
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(1)}K`;
  }
  return `$${amount.toFixed(0)}`;
};

// Helper function to format percentage
const formatPercentage = (value: number): string => {
  return `${value.toFixed(1)}%`;
};

// Helper function to format change
const formatChange = (value: number, isPercentage: boolean = false, isCurrency: boolean = false): string => {
  const sign = value >= 0 ? '+' : '';
  if (isCurrency) {
    return `${sign}${formatCurrency(Math.abs(value))}`;
  }
  if (isPercentage) {
    return `${sign}${value.toFixed(1)}%`;
  }
  return `${sign}${value}`;
};

export default function Dashboard() {
  const { data: dashboardData, isLoading, error, refetch } = useDashboardOverview();
  const { data: apiHealthy } = useApiHealth();
  
  // Modal states
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [migrationModalOpen, setMigrationModalOpen] = useState(false);
  const [reportModalOpen, setReportModalOpen] = useState(false);

  // Handle action button clicks
  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'migration':
        setMigrationModalOpen(true);
        break;
      case 'upload':
        setUploadModalOpen(true);
        break;
      case 'report':
        setReportModalOpen(true);
        break;
      default:
        toast.info(`Action: ${action}`);
    }
  };

  if (error) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4">
            <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto" />
            <div>
              <h3 className="text-lg font-medium">Unable to load dashboard</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {apiHealthy === false 
                  ? 'Backend API is not available. Please ensure the backend server is running on localhost:8000.'
                  : error instanceof Error 
                    ? error.message 
                    : 'An unexpected error occurred'
                }
              </p>
              <Button 
                variant="outline" 
                onClick={() => refetch()} 
                className="mt-4"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm opacity-80">Loading...</span>
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold mb-1">
                    {dashboardData?.metrics?.tables_processed_today?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm opacity-80">Tables Processed Today</div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {isLoading ? (
          // Loading skeleton
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="metrics-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                    <div className="h-8 w-16 bg-muted rounded animate-pulse" />
                    <div className="h-4 w-12 bg-muted rounded animate-pulse" />
                  </div>
                  <div className="h-8 w-8 bg-muted rounded animate-pulse" />
                </div>
              </CardContent>
            </Card>
          ))
        ) : dashboardData?.metrics ? (
          // Real metrics from API
          [
            {
              title: "Data Quality Score",
              value: formatPercentage(dashboardData.metrics.data_quality_score),
              change: dashboardData.metrics.change_data_quality,
              icon: CheckCircle,
              color: "text-success"
            },
            {
              title: "Active Migrations",
              value: dashboardData.metrics.active_migrations.toString(),
              change: dashboardData.metrics.change_migrations,
              icon: GitBranch,
              color: "text-primary"
            },
            {
              title: "Success Rate",
              value: formatPercentage(dashboardData.metrics.success_rate),
              change: dashboardData.metrics.change_success_rate,
              icon: TrendingUp,
              color: "text-success"
            },
            {
              title: "Cost Savings",
              value: formatCurrency(dashboardData.metrics.cost_savings),
              change: dashboardData.metrics.change_cost_savings,
              icon: DollarSign,
              color: "text-success"
            }
          ].map((metric) => (
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
          ))
        ) : (
          // Fallback when no data
          <div className="col-span-4 text-center py-8">
            <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground">No metrics data available</p>
          </div>
        )}
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
                {isLoading ? (
                  // Loading skeleton
                  Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="flex items-start space-x-4 p-3 rounded-lg border border-border/50">
                      <div className="h-5 w-5 bg-muted rounded animate-pulse mt-0.5" />
                      <div className="flex-1 space-y-2">
                        <div className="h-4 w-3/4 bg-muted rounded animate-pulse" />
                        <div className="flex items-center space-x-2">
                          <div className="h-4 w-16 bg-muted rounded animate-pulse" />
                          <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                        </div>
                      </div>
                    </div>
                  ))
                ) : dashboardData?.activities?.length ? (
                  dashboardData.activities.map((activity) => (
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
                        {activity.type === 'info' && (
                          <Database className="h-5 w-5 text-primary mt-0.5" />
                        )}
                        {activity.type === 'success' && (
                          <CheckCircle className="h-5 w-5 text-success mt-0.5" />
                        )}
                        {activity.type === 'warning' && (
                          <AlertTriangle className="h-5 w-5 text-warning mt-0.5" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">
                          {activity.title}
                        </p>
                        {activity.description && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {activity.description}
                          </p>
                        )}
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
                          {activity.user && (
                            <>
                              <span className="text-xs text-muted-foreground">•</span>
                              <span className="text-xs text-muted-foreground">
                                {activity.user}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <Clock className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-muted-foreground">No recent activities</p>
                  </div>
                )}
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
                  onClick={() => handleQuickAction(action.action)}
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

          {/* System Status */}
          <Card className="enterprise-card mt-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="h-5 w-5 mr-2" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoading ? (
                // Loading skeleton
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex justify-between">
                      <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                      <div className="h-4 w-16 bg-muted rounded animate-pulse" />
                    </div>
                    <div className="h-2 w-full bg-muted rounded animate-pulse" />
                  </div>
                ))
              ) : dashboardData?.system_status ? (
                <>
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
                    <span>{dashboardData.system_status.performance?.active_users || 0} active users</span>
                  </div>
                </>
              ) : (
                <div className="text-center py-4">
                  <Database className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">System status unavailable</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Modals */}
      <FileUploadModal 
        open={uploadModalOpen} 
        onOpenChange={setUploadModalOpen} 
      />
      <MigrationModal 
        open={migrationModalOpen} 
        onOpenChange={setMigrationModalOpen} 
      />
      <ReportModal 
        open={reportModalOpen} 
        onOpenChange={setReportModalOpen} 
      />
    </div>
  );
}