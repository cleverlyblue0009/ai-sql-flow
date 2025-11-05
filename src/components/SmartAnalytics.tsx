import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Zap, 
  AlertTriangle, 
  TrendingUp, 
  GitBranch,
  Activity,
  BarChart3,
  Sparkles,
  Brain,
  Target,
  ArrowRight
} from "lucide-react";
import { api } from "@/lib/api";

export default function SmartAnalytics() {
  // Fetch Smart Analytics data
  const { data: queryOptimizer, isLoading: loadingOptimizer } = useQuery({
    queryKey: ['smart-analytics-query-optimizer'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/smart-analytics/query-optimizer');
      return response.json();
    },
    refetchInterval: 30000,
  });

  const { data: anomalies, isLoading: loadingAnomalies } = useQuery({
    queryKey: ['smart-analytics-anomalies'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/smart-analytics/anomalies');
      return response.json();
    },
    refetchInterval: 15000,
  });

  const { data: activityIntelligence, isLoading: loadingActivity } = useQuery({
    queryKey: ['smart-analytics-activity'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/smart-analytics/activity-intelligence');
      return response.json();
    },
    refetchInterval: 30000,
  });

  const { data: performance, isLoading: loadingPerformance } = useQuery({
    queryKey: ['smart-analytics-performance'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/smart-analytics/performance-insights');
      return response.json();
    },
    refetchInterval: 30000,
  });

  if (loadingOptimizer || loadingAnomalies || loadingActivity || loadingPerformance) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="neon-spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero Header with Neon Effect */}
      <div className="relative">
        <div className="neon-backdrop absolute inset-0 opacity-30 rounded-lg"></div>
        <div className="relative z-10">
          <h1 className="text-4xl font-bold mb-2 neon-gradient-text neon-title">
            🔮 Smart Analytics
          </h1>
          <p className="text-lg text-muted-foreground">
            AI-powered insights, pattern detection, and data intelligence hub
          </p>
        </div>
      </div>

      {/* Top Row: Query Optimizer & Anomaly Detector */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Query Optimizer Advisor */}
        <Card className="neon-card">
          <CardHeader>
            <CardTitle className="flex items-center text-xl">
              <Brain className="h-6 w-6 mr-2 neon-icon" />
              <span className="neon-text">SQL Query Optimizer</span>
            </CardTitle>
            <CardDescription>
              Analyzes conversion patterns and provides optimization recommendations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Conversion Heatmap */}
            <div>
              <h4 className="text-sm font-semibold mb-3 neon-text-purple">Dialect Conversion Heatmap</h4>
              <div className="grid grid-cols-3 gap-2">
                {queryOptimizer?.data?.conversion_heatmap?.slice(0, 9).map((item: any, index: number) => (
                  <div
                    key={index}
                    className="neon-metric-card p-3 text-center"
                    style={{
                      opacity: Math.min(0.4 + (item[2] / 50), 1)
                    }}
                  >
                    <div className="text-xs text-muted-foreground">{item[0]} → {item[1]}</div>
                    <div className="text-lg font-bold neon-text-cyan">{item[2]}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Optimization Suggestions */}
            <div>
              <h4 className="text-sm font-semibold mb-3 neon-text-lime">Optimization Suggestions</h4>
              <div className="space-y-2">
                {queryOptimizer?.data?.optimization_suggestions?.map((suggestion: any, index: number) => (
                  <div key={index} className="neon-activity-item p-3 rounded-lg border border-border/30">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={`neon-badge-${
                            suggestion.impact === 'high' ? 'pink' : 
                            suggestion.impact === 'medium' ? 'purple' : 'lime'
                          }`}>
                            {suggestion.impact} impact
                          </Badge>
                          <span className="text-sm font-medium">{suggestion.title}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">{suggestion.description}</p>
                      </div>
                      <Sparkles className="h-4 w-4 neon-icon-purple flex-shrink-0 ml-2" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Confidence Scores */}
            <div className="neon-card-purple p-4">
              <h4 className="text-sm font-semibold mb-3">Average Confidence Score</h4>
              <div className="flex items-center justify-between">
                <span className="text-3xl font-bold neon-text-purple">
                  {queryOptimizer?.data?.confidence_scores?.average}%
                </span>
                <TrendingUp className="h-8 w-8 neon-icon-purple" />
              </div>
              <div className="mt-3">
                <div className="neon-progress">
                  <div 
                    className="neon-progress-bar h-2"
                    style={{ width: `${queryOptimizer?.data?.confidence_scores?.average}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Anomaly Detector */}
        <Card className="neon-card-purple">
          <CardHeader>
            <CardTitle className="flex items-center text-xl">
              <AlertTriangle className="h-6 w-6 mr-2 neon-icon-pink" />
              <span className="neon-text-purple">Data Quality Anomaly Detector</span>
            </CardTitle>
            <CardDescription>
              Real-time anomaly detection and suspicious pattern identification
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="neon-card-lime p-4">
                <div className="text-sm text-muted-foreground mb-1">Files Analyzed</div>
                <div className="text-2xl font-bold neon-text-lime">
                  {anomalies?.data?.summary?.total_files_analyzed || 0}
                </div>
              </div>
              <div className="neon-card-purple p-4">
                <div className="text-sm text-muted-foreground mb-1">Anomalies Found</div>
                <div className="text-2xl font-bold neon-text-pink">
                  {anomalies?.data?.summary?.anomalies_detected || 0}
                </div>
              </div>
            </div>

            {/* Anomaly List */}
            <div>
              <h4 className="text-sm font-semibold mb-3 neon-text-pink">Detected Anomalies</h4>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {anomalies?.data?.anomalies?.length > 0 ? (
                  anomalies.data.anomalies.map((anomaly: any, index: number) => (
                    <div 
                      key={index} 
                      className={`p-4 rounded-lg border-2 ${
                        anomaly.severity === 'high' 
                          ? 'neon-alert border-l-4' 
                          : 'border-border/50'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <span className="font-medium text-sm">{anomaly.file_name}</span>
                          <Badge className={`ml-2 neon-badge-${anomaly.severity === 'high' ? 'pink' : 'purple'}`}>
                            {anomaly.severity}
                          </Badge>
                        </div>
                        <span className="text-xl font-bold neon-text-pink">
                          {anomaly.anomaly_score}
                        </span>
                      </div>
                      <div className="space-y-1">
                        {anomaly.detected_issues?.map((issue: string, i: number) => (
                          <div key={i} className="text-xs text-muted-foreground flex items-center gap-2">
                            <AlertTriangle className="h-3 w-3" />
                            {issue}
                          </div>
                        ))}
                      </div>
                      <div className="mt-2 flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">
                          Confidence: {anomaly.confidence}%
                        </span>
                        <span className="text-muted-foreground">
                          {new Date(anomaly.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 neon-card-lime p-4">
                    <Sparkles className="h-12 w-12 mx-auto mb-2 neon-icon-lime" />
                    <p className="text-muted-foreground">No anomalies detected - all systems optimal!</p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Intelligence - Full Width */}
      <Card className="neon-card-lime">
        <CardHeader>
          <CardTitle className="flex items-center text-xl">
            <GitBranch className="h-6 w-6 mr-2 neon-icon-lime" />
            <span className="neon-text-lime">Activity Intelligence Dashboard</span>
          </CardTitle>
          <CardDescription>
            Correlates activities across Clean Data and SQL Conversion features
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Suggested Actions */}
          <div>
            <h4 className="text-sm font-semibold mb-4 neon-text-cyan">AI-Suggested Next Actions</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {activityIntelligence?.data?.suggested_actions?.map((action: any, index: number) => (
                <div key={index} className="neon-metric-card">
                  <div className="flex items-start justify-between mb-3">
                    <Badge className={`neon-badge-${
                      action.priority === 'high' ? 'pink' : 
                      action.priority === 'medium' ? 'purple' : 'lime'
                    }`}>
                      {action.priority}
                    </Badge>
                    <Target className="h-5 w-5 neon-icon-cyan" />
                  </div>
                  <h5 className="font-semibold mb-2 text-sm">{action.title}</h5>
                  <p className="text-xs text-muted-foreground mb-3">{action.description}</p>
                  <div className="flex items-center justify-between text-xs">
                    <span className="neon-text-lime">{action.estimated_impact}</span>
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Data Lineage */}
          <div>
            <h4 className="text-sm font-semibold mb-4 neon-text-purple">Recent Data Lineage</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {activityIntelligence?.data?.data_lineage?.slice(0, 8).map((item: any, index: number) => (
                <div key={index} className="neon-card-purple p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Activity className="h-4 w-4 neon-icon-purple" />
                    <span className="text-xs font-medium truncate">{item.file_name}</span>
                  </div>
                  <div className="space-y-1 text-xs text-muted-foreground">
                    <div>Quality: <span className="neon-text-cyan">{item.quality_score}%</span></div>
                    <div>Rows: {item.row_count}</div>
                    {item.has_cleaning && (
                      <Badge className="neon-badge-lime text-xs mt-1">Cleaned</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Activity Patterns */}
          <div className="neon-card p-4">
            <h4 className="text-sm font-semibold mb-3 neon-text-cyan">Activity Patterns</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-muted-foreground mb-1">Avg Files/Day</div>
                <div className="text-xl font-bold neon-text-cyan">
                  {activityIntelligence?.data?.activity_patterns?.avg_files_per_day}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">Peak Day</div>
                <div className="text-xl font-bold neon-text-purple">
                  {activityIntelligence?.data?.activity_patterns?.peak_activity_day}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">Most Active Hours</div>
                <div className="flex gap-1 mt-1">
                  {activityIntelligence?.data?.activity_patterns?.most_active_hours?.map((hour: number) => (
                    <Badge key={hour} className="neon-badge-lime text-xs">{hour}h</Badge>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">File Types</div>
                <div className="flex gap-1 mt-1 flex-wrap">
                  {activityIntelligence?.data?.activity_patterns?.common_file_types?.map((type: string) => (
                    <Badge key={type} className="neon-badge text-xs">{type}</Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bottom Row: Performance Insights */}
      <Card className="neon-card">
        <CardHeader>
          <CardTitle className="flex items-center text-xl">
            <BarChart3 className="h-6 w-6 mr-2 neon-icon-cyan" />
            <span className="neon-text-cyan">Performance Insights</span>
          </CardTitle>
          <CardDescription>
            Tracks processing efficiency and optimization opportunities
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Quality Metrics */}
          {performance?.data?.quality_metrics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="neon-metric-card">
                <div className="text-sm text-muted-foreground mb-2">Avg Quality Score</div>
                <div className="text-3xl font-bold neon-text-cyan">
                  {performance.data.quality_metrics.avg_quality_score}%
                </div>
              </div>
              <div className="neon-metric-card">
                <div className="text-sm text-muted-foreground mb-2">Avg Improvement</div>
                <div className="text-3xl font-bold neon-text-lime">
                  +{performance.data.quality_metrics.avg_improvement}%
                </div>
              </div>
              <div className="neon-metric-card">
                <div className="text-sm text-muted-foreground mb-2">Files Processed</div>
                <div className="text-3xl font-bold neon-text-purple">
                  {performance.data.quality_metrics.total_files_processed}
                </div>
              </div>
              <div className="neon-metric-card">
                <div className="text-sm text-muted-foreground mb-2">Efficiency Score</div>
                <div className="text-3xl font-bold neon-gradient-text">
                  {performance.data.efficiency_score}%
                </div>
              </div>
            </div>
          )}

          {/* Optimization Opportunities */}
          {performance?.data?.optimization_opportunities && (
            <div>
              <h4 className="text-sm font-semibold mb-3 neon-text-lime">Optimization Opportunities</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {performance.data.optimization_opportunities.map((opp: any, index: number) => (
                  <div key={index} className="neon-card-lime p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h5 className="font-semibold text-sm">{opp.title}</h5>
                      <Zap className="h-5 w-5 neon-icon-lime" />
                    </div>
                    <p className="text-xs text-muted-foreground mb-3">{opp.description}</p>
                    <div className="neon-badge-lime text-xs">{opp.potential_savings}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottlenecks */}
          {performance?.data?.bottlenecks?.length > 0 && (
            <div className="neon-alert p-4">
              <h4 className="text-sm font-semibold mb-3 flex items-center">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Detected Bottlenecks
              </h4>
              <div className="space-y-2">
                {performance.data.bottlenecks.map((bottleneck: any, index: number) => (
                  <div key={index} className="text-sm">
                    <span className="font-medium">{bottleneck.area}:</span> {bottleneck.description}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
