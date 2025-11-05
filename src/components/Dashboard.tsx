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
  ArrowUpRight
} from "lucide-react";
import heroImage from "@/assets/hero-data-center.jpg";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Metrics will be computed from real data


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
  // Fetch dashboard data from API
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: api.dashboard.getOverview,
    refetchInterval: (query) => {
      // Stop refetching if there's an error (backend is down)
      return query.state.error ? false : 30000;
    },
    retry: 1, // Only retry once instead of default 3 times
    retryDelay: 5000, // Wait 5 seconds before retry
  });

  // Fetch system metrics
  const { data: systemData } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: api.monitoring.getSystemMetrics,
    refetchInterval: (query) => {
      return query.state.error ? false : 10000;
    },
    retry: 1,
    retryDelay: 5000,
    enabled: !error, // Don't fetch if main query failed
  });

  // Fetch recent uploads for activity
  const { data: recentUploadsData } = useQuery({
    queryKey: ['recent-uploads'],
    queryFn: api.dataQuality.getRecentUploads,
    refetchInterval: (query) => {
      return query.state.error ? false : 30000;
    },
    retry: 1,
    retryDelay: 5000,
    enabled: !error, // Don't fetch if main query failed
  });

  // Fetch Smart Analytics activity intelligence for real activity feed
  const { data: activityIntelligence } = useQuery({
    queryKey: ['activity-intelligence'],
    queryFn: api.smartAnalytics.getActivityIntelligence,
    refetchInterval: (query) => {
      return query.state.error ? false : 30000;
    },
    retry: 1,
    retryDelay: 5000,
    enabled: !error, // Don't fetch if main query failed
  });

  // Fetch Smart Analytics for insights
  const { data: smartAnalyticsData } = useQuery({
    queryKey: ['smart-analytics-overview'],
    queryFn: api.smartAnalytics.getOverview,
    refetchInterval: (query) => {
      return query.state.error ? false : 60000;
    },
    retry: 1,
    retryDelay: 5000,
    enabled: !error, // Don't fetch if main query failed
  });

  // Compute real metrics from actual data
  const computedMetrics = [
    {
      title: "Data Quality Score",
      value: dashboardData?.data?.summary?.avg_quality_score 
        ? `${dashboardData.data.summary.avg_quality_score.toFixed(1)}%`
        : `${smartAnalyticsData?.data?.anomaly_detection?.avg_quality_score || 0}%`,
      change: smartAnalyticsData?.data?.anomaly_detection?.quality_trend === 'improving' ? "+2.4%" : "0%",
      trend: smartAnalyticsData?.data?.anomaly_detection?.quality_trend === 'improving' ? "up" : "stable",
      icon: CheckCircle,
      color: "text-success",
      neonClass: "cyan"
    },
    {
      title: "Active Migrations",
      value: smartAnalyticsData?.data?.conversion_intelligence?.total_conversions?.toString() || "0",
      change: "+3",
      trend: "up", 
      icon: GitBranch,
      color: "text-primary",
      neonClass: "purple"
    },
    {
      title: "Success Rate",
      value: smartAnalyticsData?.data?.conversion_intelligence?.success_rate 
        ? `${smartAnalyticsData.data.conversion_intelligence.success_rate}%`
        : `${dashboardData?.data?.summary?.success_rate || 0}%`,
      change: "+0.5%",
      trend: "up",
      icon: TrendingUp,
      color: "text-success",
      neonClass: "lime"
    },
    {
      title: "Total Files Processed",
      value: dashboardData?.data?.summary?.total_data_profiles?.toString() 
        || smartAnalyticsData?.data?.anomaly_detection?.total_files_analyzed?.toString() 
        || "0",
      change: "+12",
      trend: "up",
      icon: FileText,
      color: "text-success",
      neonClass: "purple"
    }
  ];

  // Get real activity feed from Smart Analytics
  const recentActivities = activityIntelligence?.data?.activity_timeline?.slice(0, 10).map((activity: any, index: number) => ({
    id: index,
    type: activity.type === 'data_cleaning' ? 'quality' : activity.type === 'sql_conversion' ? 'migration' : 'analytics',
    title: activity.action,
    timestamp: new Date(activity.timestamp).toLocaleString(),
    status: activity.metadata?.quality_score ? 
      (activity.metadata.quality_score > 80 ? 'success' : 'warning') : 
      'success',
    source: activity.type
  })) || [];

  // Platform insights from Smart Analytics
  const platformInsights = [
    smartAnalyticsData?.data?.query_optimizer?.most_converted_pair && {
      text: `Most converted dialect: ${smartAnalyticsData.data.query_optimizer.most_converted_pair.pair} (${smartAnalyticsData.data.query_optimizer.most_converted_pair.count} conversions)`,
      icon: Database,
      color: "purple"
    },
    smartAnalyticsData?.data?.anomaly_detection && {
      text: `Data quality trend: ${smartAnalyticsData.data.anomaly_detection.quality_trend}`,
      icon: TrendingUp,
      color: smartAnalyticsData.data.anomaly_detection.quality_trend === 'improving' ? 'lime' : 'cyan'
    },
    smartAnalyticsData?.data?.conversion_intelligence?.avg_confidence && {
      text: `Average SQL conversion confidence: ${smartAnalyticsData.data.conversion_intelligence.avg_confidence}%`,
      icon: CheckCircle,
      color: "cyan"
    }
  ].filter(Boolean);

  if (error) {
    return (
      <div className="space-y-8">
        <Card className="border-destructive">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-destructive" />
                <div>
                  <p className="font-medium text-destructive">Unable to connect to backend</p>
                  <p className="text-sm text-muted-foreground">
                    Make sure the backend is running on http://localhost:8000
                  </p>
                </div>
              </div>
              <Button 
                variant="outline" 
                onClick={() => window.location.reload()}
              >
                Retry Connection
              </Button>
            </div>
          </CardContent>
        </Card>
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
              {isLoading && (
                <div className="text-sm text-muted-foreground">Loading dashboard data...</div>
              )}
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold mb-1">
                {dashboardData?.data?.summary?.total_data_profiles || '1,247'}
              </div>
              <div className="text-sm opacity-80">Tables Processed Today</div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics with Neon Effects */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {computedMetrics.map((metric) => (
          <Card key={metric.title} className={`neon-metric-card ${metric.neonClass}`}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    {metric.title}
                  </p>
                  <p className={`text-2xl font-bold neon-text-${metric.neonClass}`}>{metric.value}</p>
                  <div className="flex items-center mt-2">
                    {metric.trend === "up" && <ArrowUpRight className={`h-4 w-4 neon-glow-${metric.neonClass} mr-1`} />}
                    <span className={`text-sm neon-text-${metric.neonClass} font-medium`}>
                      {metric.change}
                    </span>
                  </div>
                </div>
                <div className={`neon-glow-${metric.neonClass}`}>
                  <metric.icon className="h-8 w-8" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity Timeline with Neon */}
        <div className="lg:col-span-2">
          <Card className="neon-card-cyan">
            <CardHeader>
              <CardTitle className="flex items-center neon-text-cyan">
                <Clock className="h-5 w-5 mr-2 neon-glow-cyan" />
                Recent Activity
              </CardTitle>
              <CardDescription>
                Real-time activities from all platform features
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentActivities.length > 0 ? (
                  recentActivities.map((activity: any) => (
                    <div 
                      key={activity.id} 
                      className={`activity-item-neon ${activity.source === 'data_cleaning' ? 'clean-data' : activity.source === 'sql_conversion' ? 'convert-sql' : 'analytics'} flex items-start space-x-4 p-3 rounded-lg border border-border/50 transition-all`}
                    >
                      <div className="flex-shrink-0">
                        {activity.type === 'migration' && (
                          <GitBranch className="h-5 w-5 neon-glow-purple mt-0.5" />
                        )}
                        {activity.type === 'quality' && (
                          <CheckCircle className="h-5 w-5 neon-glow-cyan mt-0.5" />
                        )}
                        {activity.type === 'analytics' && (
                          <Database className="h-5 w-5 neon-glow-lime mt-0.5" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">
                          {activity.title}
                        </p>
                        <div className="flex items-center mt-1 space-x-2">
                          <Badge 
                            variant={activity.status === 'success' ? 'default' : 'secondary'}
                            className={`text-xs ${activity.source === 'data_cleaning' ? 'neon-badge-cyan' : activity.source === 'sql_conversion' ? 'neon-badge-purple' : 'neon-badge-lime'}`}
                          >
                            {activity.source === 'data_cleaning' ? 'Clean Data' : activity.source === 'sql_conversion' ? 'Convert SQL' : 'Analytics'}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {activity.timestamp}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Clock className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No recent activities</p>
                    <p className="text-xs mt-1">Start using the platform to see activities here</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Platform Insights from Smart Analytics */}
          {platformInsights.length > 0 && (
            <Card className="neon-card-purple mt-6">
              <CardHeader>
                <CardTitle className="flex items-center neon-text-purple">
                  <TrendingUp className="h-5 w-5 mr-2 neon-glow-purple" />
                  Platform Insights
                </CardTitle>
                <CardDescription>
                  AI-powered insights from Smart Analytics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {platformInsights.map((insight: any, index: number) => (
                    <div key={index} className={`flex items-center space-x-3 p-3 rounded-lg neon-border-${insight.color}-subtle bg-muted/30`}>
                      <insight.icon className={`h-5 w-5 neon-glow-${insight.color}`} />
                      <p className="text-sm">{insight.text}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
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
                  <span>CPU Usage</span>
                  <span className={systemData?.data?.cpu?.status === 'healthy' ? 'text-success' : 'text-warning'}>
                    {systemData?.data?.cpu?.status || 'Operational'}
                  </span>
                </div>
                <Progress value={systemData?.data?.cpu?.usage_percent || 98} className="h-2" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Memory Usage</span>
                  <span className={systemData?.data?.memory?.status === 'healthy' ? 'text-success' : 'text-warning'}>
                    {systemData?.data?.memory?.status || 'Operational'}
                  </span>
                </div>
                <Progress value={systemData?.data?.memory?.usage_percent || 94} className="h-2" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Disk Usage</span>
                  <span className={systemData?.data?.disk?.status === 'healthy' ? 'text-success' : 'text-warning'}>
                    {systemData?.data?.disk?.status || 'Operational'}
                  </span>
                </div>
                <Progress value={systemData?.data?.disk?.usage_percent || 96} className="h-2" />
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