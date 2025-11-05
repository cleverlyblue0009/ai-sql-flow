import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Sparkles, 
  TrendingUp, 
  AlertTriangle, 
  Activity, 
  Database,
  Zap,
  BarChart3,
  RefreshCw,
  ArrowUpRight,
  CheckCircle,
  AlertCircle
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function SmartAnalytics() {
  // Fetch all analytics data
  const { data: queryOptimizerData, refetch: refetchOptimizer } = useQuery({
    queryKey: ['smart-analytics-query-optimizer'],
    queryFn: api.smartAnalytics.getQueryOptimizer,
    refetchInterval: 30000,
  });

  const { data: anomalyData, refetch: refetchAnomalies } = useQuery({
    queryKey: ['smart-analytics-anomalies'],
    queryFn: api.smartAnalytics.getAnomalyDetection,
    refetchInterval: 30000,
  });

  const { data: activityData, refetch: refetchActivity } = useQuery({
    queryKey: ['smart-analytics-activity'],
    queryFn: api.smartAnalytics.getActivityIntelligence,
    refetchInterval: 30000,
  });

  const { data: conversionData } = useQuery({
    queryKey: ['smart-analytics-conversion'],
    queryFn: api.smartAnalytics.getConversionIntelligence,
    refetchInterval: 30000,
  });

  const { data: performanceData } = useQuery({
    queryKey: ['smart-analytics-performance'],
    queryFn: api.smartAnalytics.getPerformanceInsights,
    refetchInterval: 30000,
  });

  const handleRefreshAll = () => {
    refetchOptimizer();
    refetchAnomalies();
    refetchActivity();
  };

  return (
    <div className="space-y-8">
      {/* Header with neon glow */}
      <div className="neon-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2 neon-text-cyan">
              <Sparkles className="inline-block h-8 w-8 mr-3 neon-glow-cyan" />
              Smart Analytics
            </h1>
            <p className="text-lg opacity-90">
              AI-powered insights, pattern detection, and predictive analytics
            </p>
          </div>
          <Button 
            onClick={handleRefreshAll}
            className="neon-button-cyan"
            variant="outline"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Top Row: Query Optimizer & Anomaly Detector */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Query Optimizer Advisor */}
        <Card className="neon-card-cyan">
          <CardHeader>
            <CardTitle className="flex items-center neon-text-cyan">
              <BarChart3 className="h-5 w-5 mr-2" />
              SQL Query Optimizer Advisor
            </CardTitle>
            <CardDescription>
              Analyze SQL conversion patterns and optimization opportunities
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 rounded-lg bg-muted/30 neon-border-cyan-subtle">
                <div className="text-2xl font-bold neon-text-cyan">
                  {queryOptimizerData?.data?.total_conversions || 0}
                </div>
                <div className="text-xs text-muted-foreground">Total Conversions</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted/30 neon-border-purple-subtle">
                <div className="text-2xl font-bold neon-text-purple">
                  {queryOptimizerData?.data?.avg_confidence || 0}%
                </div>
                <div className="text-xs text-muted-foreground">Avg Confidence</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted/30 neon-border-lime-subtle">
                <div className="text-2xl font-bold neon-text-lime">
                  {queryOptimizerData?.data?.dialect_heatmap?.length || 0}
                </div>
                <div className="text-xs text-muted-foreground">Dialect Pairs</div>
              </div>
            </div>

            {/* Dialect Heatmap */}
            {queryOptimizerData?.data?.dialect_heatmap && queryOptimizerData.data.dialect_heatmap.length > 0 ? (
              <div className="space-y-3">
                <h4 className="font-medium text-sm">Most Converted Dialect Pairs</h4>
                {queryOptimizerData.data.dialect_heatmap.slice(0, 5).map((pair: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-2 rounded-lg border border-border/50 hover:neon-glow-cyan-subtle transition-all">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 rounded-full neon-glow-cyan"></div>
                      <span className="text-sm font-medium">{pair.pair}</span>
                    </div>
                    <Badge variant="outline" className="neon-border-cyan-subtle">
                      {pair.count} conversions
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Database className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No conversion data yet</p>
                <p className="text-xs mt-1">Start converting SQL to see insights</p>
              </div>
            )}

            {/* Recommendations */}
            {queryOptimizerData?.data?.recommendations && queryOptimizerData.data.recommendations.length > 0 && (
              <div className="p-4 bg-muted/30 rounded-lg neon-border-purple-subtle">
                <h4 className="font-medium text-sm mb-2 neon-text-purple">💡 AI Recommendations</h4>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  {queryOptimizerData.data.recommendations.map((rec: string, index: number) => (
                    <li key={index}>• {rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Anomaly Detector */}
        <Card className="neon-card-purple">
          <CardHeader>
            <CardTitle className="flex items-center neon-text-purple">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Data Quality Anomaly Detector
            </CardTitle>
            <CardDescription>
              Real-time ML-powered anomaly detection
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Health Status */}
            <div className="flex items-center justify-between p-4 rounded-lg neon-border-purple-subtle bg-muted/30">
              <div className="flex items-center space-x-3">
                {anomalyData?.data?.health_status === 'healthy' ? (
                  <CheckCircle className="h-6 w-6 neon-glow-lime" />
                ) : anomalyData?.data?.health_status === 'warning' ? (
                  <AlertCircle className="h-6 w-6 neon-glow-pink" />
                ) : (
                  <AlertTriangle className="h-6 w-6 neon-glow-pink" />
                )}
                <div>
                  <div className="font-medium">System Health</div>
                  <div className="text-sm text-muted-foreground">
                    {anomalyData?.data?.anomaly_count || 0} anomalies detected
                  </div>
                </div>
              </div>
              <Badge 
                variant={anomalyData?.data?.health_status === 'healthy' ? 'default' : 'destructive'}
                className={anomalyData?.data?.health_status === 'healthy' ? 'neon-border-lime-subtle' : 'neon-border-pink'}
              >
                {anomalyData?.data?.health_status || 'Unknown'}
              </Badge>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 rounded-lg bg-muted/30 neon-border-purple-subtle">
                <div className="text-2xl font-bold neon-text-purple">
                  {anomalyData?.data?.avg_quality_score || 0}%
                </div>
                <div className="text-xs text-muted-foreground">Avg Quality</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted/30 neon-border-cyan-subtle">
                <div className="text-2xl font-bold neon-text-cyan">
                  {anomalyData?.data?.total_files_analyzed || 0}
                </div>
                <div className="text-xs text-muted-foreground">Files Analyzed</div>
              </div>
            </div>

            {/* Anomalies List */}
            {anomalyData?.data?.anomalies_detected && anomalyData.data.anomalies_detected.length > 0 ? (
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Detected Anomalies</h4>
                {anomalyData.data.anomalies_detected.slice(0, 3).map((anomaly: any, index: number) => (
                  <div 
                    key={index} 
                    className="p-3 rounded-lg border-l-4 border-l-pink-500 bg-pink-500/5 neon-pulse-pink-subtle"
                  >
                    <div className="flex items-start justify-between mb-1">
                      <div className="font-medium text-sm">{anomaly.file_name}</div>
                      <Badge variant="destructive" className="text-xs neon-border-pink">
                        {anomaly.quality_score}% quality
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground space-y-1">
                      {anomaly.detected_issues?.slice(0, 2).map((issue: string, i: number) => (
                        <div key={i}>• {issue}</div>
                      ))}
                    </div>
                    <div className="mt-2 text-xs">
                      Confidence: <span className="font-medium">{(anomaly.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <CheckCircle className="h-12 w-12 mx-auto mb-2 neon-glow-lime" />
                <p className="font-medium">All Clear!</p>
                <p className="text-xs mt-1">No anomalies detected in your data</p>
              </div>
            )}

            {/* Trend */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 neon-border-lime-subtle">
              <span className="text-sm">Quality Trend</span>
              <div className="flex items-center space-x-2">
                {anomalyData?.data?.quality_trend === 'improving' && (
                  <>
                    <TrendingUp className="h-4 w-4 neon-glow-lime" />
                    <span className="text-sm font-medium neon-text-lime">Improving</span>
                  </>
                )}
                {anomalyData?.data?.quality_trend === 'declining' && (
                  <>
                    <TrendingUp className="h-4 w-4 rotate-180 neon-glow-pink" />
                    <span className="text-sm font-medium neon-text-pink">Declining</span>
                  </>
                )}
                {anomalyData?.data?.quality_trend === 'stable' && (
                  <span className="text-sm font-medium text-muted-foreground">Stable</span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Intelligence Dashboard */}
      <Card className="neon-card-lime">
        <CardHeader>
          <CardTitle className="flex items-center neon-text-lime">
            <Activity className="h-5 w-5 mr-2" />
            Activity Intelligence Dashboard
          </CardTitle>
          <CardDescription>
            Correlate activities across Clean Data and SQL Conversion features
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Activity Timeline */}
            <div className="space-y-4">
              <h4 className="font-medium">Recent Activity Timeline</h4>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {activityData?.data?.activity_timeline && activityData.data.activity_timeline.length > 0 ? (
                  activityData.data.activity_timeline.slice(0, 10).map((activity: any, index: number) => (
                    <div 
                      key={index} 
                      className="flex items-start space-x-3 p-3 rounded-lg border border-border/50 hover:neon-glow-lime-subtle transition-all neon-border-lime-subtle"
                    >
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        activity.type === 'data_cleaning' ? 'neon-glow-cyan' : 'neon-glow-purple'
                      }`}></div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{activity.action}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(activity.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <Badge 
                        variant="outline" 
                        className={activity.type === 'data_cleaning' ? 'neon-border-cyan-subtle' : 'neon-border-purple-subtle'}
                      >
                        {activity.type === 'data_cleaning' ? 'Clean' : 'Convert'}
                      </Badge>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No activities yet</p>
                  </div>
                )}
              </div>
            </div>

            {/* Insights & Suggestions */}
            <div className="space-y-4">
              <h4 className="font-medium">AI Insights & Suggestions</h4>
              
              {/* Detected Patterns */}
              {activityData?.data?.detected_patterns && activityData.data.detected_patterns.length > 0 && (
                <div className="p-4 rounded-lg bg-muted/30 neon-border-cyan-subtle">
                  <h5 className="text-sm font-medium mb-2 neon-text-cyan">🎯 Detected Patterns</h5>
                  {activityData.data.detected_patterns.map((pattern: any, index: number) => (
                    <div key={index} className="text-sm text-muted-foreground mb-2">
                      • {pattern.description}
                      <span className="ml-2 text-xs">({(pattern.confidence * 100).toFixed(0)}% confidence)</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Next Actions */}
              {activityData?.data?.next_suggested_actions && activityData.data.next_suggested_actions.length > 0 && (
                <div className="space-y-2">
                  <h5 className="text-sm font-medium neon-text-purple">💡 Suggested Next Actions</h5>
                  {activityData.data.next_suggested_actions.map((suggestion: any, index: number) => (
                    <div 
                      key={index} 
                      className="p-3 rounded-lg border border-border/50 neon-border-purple-subtle hover:neon-glow-purple-subtle transition-all"
                    >
                      <div className="flex items-start justify-between mb-1">
                        <div className="font-medium text-sm">{suggestion.title}</div>
                        <Badge variant="outline" className="text-xs">
                          {suggestion.priority}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{suggestion.description}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Activity Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-muted/30 text-center neon-border-lime-subtle">
                  <div className="text-lg font-bold neon-text-lime">
                    {activityData?.data?.total_activities || 0}
                  </div>
                  <div className="text-xs text-muted-foreground">Total Activities</div>
                </div>
                <div className="p-3 rounded-lg bg-muted/30 text-center neon-border-cyan-subtle">
                  <div className="text-lg font-bold neon-text-cyan capitalize">
                    {activityData?.data?.activity_frequency || 'N/A'}
                  </div>
                  <div className="text-xs text-muted-foreground">Activity Level</div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bottom Row: Conversion Intelligence & Performance Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversion Intelligence Report */}
        <Card className="neon-card-purple">
          <CardHeader>
            <CardTitle className="flex items-center neon-text-purple">
              <Database className="h-5 w-5 mr-2" />
              Conversion Intelligence Report
            </CardTitle>
            <CardDescription>
              SQL migration success rates and dialect insights
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Overall Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 rounded-lg bg-muted/30 neon-border-purple-subtle">
                <div className="text-3xl font-bold neon-text-purple">
                  {conversionData?.data?.success_rate || 0}%
                </div>
                <div className="text-sm text-muted-foreground mt-1">Success Rate</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted/30 neon-border-cyan-subtle">
                <div className="text-3xl font-bold neon-text-cyan">
                  {conversionData?.data?.avg_confidence || 0}%
                </div>
                <div className="text-sm text-muted-foreground mt-1">Avg Confidence</div>
              </div>
            </div>

            {/* Most Popular Pair */}
            {conversionData?.data?.most_popular_pair && (
              <div className="p-4 rounded-lg bg-gradient-to-r from-purple-500/10 to-cyan-500/10 neon-border-purple-subtle">
                <div className="text-sm text-muted-foreground mb-1">🔥 Most Popular</div>
                <div className="text-lg font-bold neon-text-purple">
                  {conversionData.data.most_popular_pair.source} → {conversionData.data.most_popular_pair.target}
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  {conversionData.data.most_popular_pair.count} conversions • {conversionData.data.most_popular_pair.success_rate}% success
                </div>
              </div>
            )}

            {/* Dialect Pairs Table */}
            {conversionData?.data?.dialect_pairs && conversionData.data.dialect_pairs.length > 0 && (
              <div className="space-y-2">
                <h5 className="text-sm font-medium">Conversion Performance</h5>
                {conversionData.data.dialect_pairs.slice(0, 5).map((pair: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg border border-border/50 neon-border-purple-subtle">
                    <div className="flex-1">
                      <div className="text-sm font-medium">{pair.source} → {pair.target}</div>
                      <div className="text-xs text-muted-foreground">{pair.count} conversions</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium neon-text-purple">{pair.success_rate}%</div>
                      <div className="text-xs text-muted-foreground">{pair.avg_confidence}% conf</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Performance Insights */}
        <Card className="neon-card-cyan">
          <CardHeader>
            <CardTitle className="flex items-center neon-text-cyan">
              <Zap className="h-5 w-5 mr-2" />
              Performance Insights
            </CardTitle>
            <CardDescription>
              Track effectiveness across all platform features
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* SQL Conversion Performance */}
            <div className="p-4 rounded-lg bg-muted/30 neon-border-cyan-subtle">
              <h5 className="text-sm font-medium mb-3">SQL Conversion</h5>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Success Rate</span>
                    <span className="font-medium neon-text-cyan">
                      {performanceData?.data?.sql_conversion?.success_rate || 0}%
                    </span>
                  </div>
                  <Progress 
                    value={performanceData?.data?.sql_conversion?.success_rate || 0} 
                    className="h-2 neon-progress-cyan" 
                  />
                </div>
                <div className="text-xs text-muted-foreground">
                  Avg Processing Time: {performanceData?.data?.sql_conversion?.avg_processing_time_sec || 0}s
                </div>
              </div>
            </div>

            {/* Data Cleaning Performance */}
            <div className="p-4 rounded-lg bg-muted/30 neon-border-purple-subtle">
              <h5 className="text-sm font-medium mb-3">Data Cleaning</h5>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Effectiveness Score</span>
                    <span className="font-medium neon-text-purple">
                      {performanceData?.data?.data_cleaning?.effectiveness_score || 0}%
                    </span>
                  </div>
                  <Progress 
                    value={performanceData?.data?.data_cleaning?.effectiveness_score || 0} 
                    className="h-2 neon-progress-purple" 
                  />
                </div>
                <div className="text-xs text-muted-foreground">
                  Avg Quality Improvement: +{performanceData?.data?.data_cleaning?.avg_quality_improvement || 0}%
                </div>
              </div>
            </div>

            {/* Overall Performance */}
            <div className="p-4 rounded-lg bg-gradient-to-r from-cyan-500/10 to-purple-500/10 neon-border-lime-subtle">
              <h5 className="text-sm font-medium mb-3 neon-text-lime">Overall Platform Health</h5>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-muted-foreground text-xs">Uptime</div>
                  <div className="font-bold text-lg neon-text-lime">
                    {performanceData?.data?.overall_performance?.uptime_percentage || 0}%
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground text-xs">Response Time</div>
                  <div className="font-bold text-lg neon-text-cyan">
                    {performanceData?.data?.overall_performance?.avg_response_time_ms || 0}ms
                  </div>
                </div>
              </div>
            </div>

            {/* Bottlenecks */}
            {performanceData?.data?.bottlenecks && performanceData.data.bottlenecks.length > 0 && (
              <div className="p-3 rounded-lg border-l-4 border-l-pink-500 bg-pink-500/5">
                <h5 className="text-sm font-medium mb-2 neon-text-pink">⚠️ Detected Bottlenecks</h5>
                {performanceData.data.bottlenecks.map((bottleneck: any, index: number) => (
                  <div key={index} className="text-xs text-muted-foreground mb-1">
                    • {bottleneck.description}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
