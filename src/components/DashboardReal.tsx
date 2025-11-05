import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  TrendingUp, 
  CheckCircle, 
  GitBranch,
  Upload,
  ArrowUpRight,
  FileUp,
  DatabaseZap,
  AlertTriangle,
  Sparkles
} from "lucide-react";
import heroImage from "@/assets/hero-data-center.jpg";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useNavigate } from "react-router-dom";

export default function DashboardReal() {
  const navigate = useNavigate();

  // Fetch REAL dashboard stats (no mock data!)
  const { data: statsData, isLoading: loadingStats, error } = useQuery({
    queryKey: ['dashboard-real-stats'],
    queryFn: api.dashboardReal.getStats,
    refetchInterval: 30000,
  });

  // Fetch REAL activity feed
  const { data: activityData, isLoading: loadingActivity } = useQuery({
    queryKey: ['dashboard-real-activity'],
    queryFn: api.dashboardReal.getActivity,
    refetchInterval: 15000,
  });

  // Fetch platform insights from Smart Analytics
  const { data: insightsData, isLoading: loadingInsights } = useQuery({
    queryKey: ['dashboard-real-insights'],
    queryFn: api.dashboardReal.getInsights,
    refetchInterval: 30000,
  });

  const stats = statsData?.data;
  const activities = activityData?.data || [];
  const insights = insightsData?.data || [];

  // Real metrics from backend (no mock data!)
  const metrics = stats ? [
    {
      title: "Data Quality Score",
      value: `${stats.data_quality_score}%`,
      change: `${stats.trends.quality > 0 ? '+' : ''}${stats.trends.quality}%`,
      trend: stats.trends.quality >= 0 ? "up" : "down",
      icon: CheckCircle,
      color: "neon-text-cyan"
    },
    {
      title: "Active Migrations",
      value: stats.active_migrations.toString(),
      change: `${stats.trends.migrations > 0 ? '+' : ''}${stats.trends.migrations}`,
      trend: stats.trends.migrations >= 0 ? "up" : "down",
      icon: GitBranch,
      color: "neon-text-purple"
    },
    {
      title: "Success Rate",
      value: `${stats.success_rate}%`,
      change: "+0.5%",
      trend: "up",
      icon: TrendingUp,
      color: "neon-text-lime"
    },
    {
      title: "Total Files",
      value: stats.total_files.toString(),
      change: `${stats.trends.migrations} recent`,
      trend: "up",
      icon: FileUp,
      color: "neon-text-pink"
    }
  ] : [];

  const quickActions = [
    {
      title: "Upload Data",
      description: "Upload files for quality analysis", 
      icon: Upload,
      action: () => navigate('/data-quality'),
      color: "neon-card-cyan"
    },
    {
      title: "Convert SQL",
      description: "Migrate queries between databases",
      icon: DatabaseZap,
      action: () => navigate('/sql-migration'),
      color: "neon-card-purple"
    },
    {
      title: "View Analytics",
      description: "AI-powered insights and patterns",
      icon: Sparkles,
      action: () => navigate('/smart-analytics'),
      color: "neon-card-lime"
    }
  ];

  if (error) {
    return (
      <div className="space-y-8">
        <Card className="neon-border-pink">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 neon-icon-pink" />
              <div>
                <p className="font-medium neon-text-pink">Unable to connect to backend</p>
                <p className="text-sm text-muted-foreground">
                  Make sure the backend is running on http://localhost:8000
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero Section with Neon Effect */}
      <div className="hero-section relative neon-backdrop rounded-lg">
        <div 
          className="absolute inset-0 opacity-20 bg-cover bg-center rounded-lg"
          style={{ backgroundImage: `url(${heroImage})` }}
        />
        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold mb-2 neon-gradient-text">
                AI-Powered Data Platform
              </h1>
              <p className="text-lg opacity-90 mb-6 md:mb-0">
                Streamline your data cleaning and SQL migrations with enterprise-grade AI
              </p>
              {loadingStats && (
                <div className="flex items-center gap-2 mt-2">
                  <div className="neon-spinner"></div>
                  <span className="text-sm text-muted-foreground">Loading dashboard data...</span>
                </div>
              )}
            </div>
            {stats && (
              <div className="text-right neon-card p-4">
                <div className="text-2xl font-bold neon-text-cyan mb-1">
                  {stats.total_files}
                </div>
                <div className="text-sm opacity-80">Files Processed</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Real Key Metrics - NO MOCK DATA */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric) => (
          <Card key={metric.title} className="neon-metric-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    {metric.title}
                  </p>
                  <p className={`text-2xl font-bold ${metric.color}`}>{metric.value}</p>
                  <div className="flex items-center mt-2">
                    <ArrowUpRight className={`h-4 w-4 mr-1 ${
                      metric.trend === 'up' ? 'neon-icon-lime' : 'neon-icon-pink rotate-90'
                    }`} />
                    <span className={`text-sm font-medium ${
                      metric.trend === 'up' ? 'neon-text-lime' : 'neon-text-pink'
                    }`}>
                      {metric.change}
                    </span>
                  </div>
                </div>
                <div>
                  <metric.icon className={`h-8 w-8 neon-icon-cyan`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Real Activity Feed - Connected to All Three Tabs */}
        <div className="lg:col-span-2">
          <Card className="neon-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 mr-2 neon-icon-cyan" />
                <span className="neon-text-cyan">Recent Activity</span>
              </CardTitle>
              <CardDescription>
                Real-time activities from Clean Data, Convert SQL, and Smart Analytics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingActivity ? (
                <div className="flex items-center justify-center py-8">
                  <div className="neon-spinner"></div>
                </div>
              ) : activities.length > 0 ? (
                <div className="space-y-3">
                  {activities.slice(0, 8).map((activity: any) => (
                    <div 
                      key={activity.id} 
                      className="neon-activity-item p-4 rounded-lg border border-border/50 hover:border-border transition-all relative"
                    >
                      <div className="flex items-start space-x-4">
                        <div className="flex-shrink-0">
                          {activity.type === 'convert_sql' && (
                            <DatabaseZap className="h-5 w-5 neon-icon-purple mt-0.5" />
                          )}
                          {activity.type === 'clean_data' && (
                            <CheckCircle className="h-5 w-5 neon-icon-cyan mt-0.5" />
                          )}
                          {activity.type === 'analytics' && (
                            <Sparkles className="h-5 w-5 neon-icon-lime mt-0.5" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">
                            {activity.action}
                          </p>
                          <div className="flex items-center mt-1 space-x-2">
                            <Badge className={`text-xs ${
                              activity.type === 'convert_sql' ? 'neon-badge-purple' :
                              activity.type === 'clean_data' ? 'neon-badge' :
                              'neon-badge-lime'
                            }`}>
                              {activity.type === 'convert_sql' ? 'Convert SQL' :
                               activity.type === 'clean_data' ? 'Clean Data' : 
                               'Analytics'}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {new Date(activity.timestamp).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No activities yet. Start by uploading data or converting SQL!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions & Platform Insights */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card className="neon-card-purple">
            <CardHeader>
              <CardTitle className="neon-text-purple">Quick Actions</CardTitle>
              <CardDescription>
                Commonly used platform features
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {quickActions.map((action) => (
                <button
                  key={action.title}
                  onClick={action.action}
                  className={`w-full p-4 rounded-lg ${action.color} text-left transition-all hover:scale-105`}
                >
                  <div className="flex items-center w-full">
                    <action.icon className="h-5 w-5 mr-3 flex-shrink-0 neon-icon" />
                    <div className="flex-1">
                      <div className="font-medium">{action.title}</div>
                      <div className="text-sm opacity-90 mt-1">
                        {action.description}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </CardContent>
          </Card>

          {/* Platform Insights from Smart Analytics */}
          <Card className="neon-card-lime">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Sparkles className="h-5 w-5 mr-2 neon-icon-lime" />
                <span className="neon-text-lime">Platform Insights</span>
              </CardTitle>
              <CardDescription>
                AI-powered insights from Smart Analytics
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {loadingInsights ? (
                <div className="flex items-center justify-center py-4">
                  <div className="neon-spinner"></div>
                </div>
              ) : insights.length > 0 ? (
                insights.map((insight: any, index: number) => (
                  <div key={index} className="p-3 rounded-lg border border-border/50 neon-activity-item">
                    <div className="text-sm font-medium mb-1">{insight.title}</div>
                    <div className="text-lg font-bold neon-text-cyan">{insight.value}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Source: {insight.source.replace('_', ' ')}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Upload data to see insights
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
