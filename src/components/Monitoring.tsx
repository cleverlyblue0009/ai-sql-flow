import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  Activity, 
  AlertTriangle, 
  TrendingUp, 
  Clock, 
  CheckCircle,
  XCircle,
  Zap,
  Database,
  Users,
  Bell,
  Filter,
  RefreshCw
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function Monitoring() {
  // Fetch real-time metrics
  const { data: realtimeData, isLoading: isLoadingRealtime, refetch: refetchRealtime } = useQuery({
    queryKey: ['monitoring-realtime'],
    queryFn: api.monitoring.getRealtimeMetrics,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Fetch service status
  const { data: serviceData, isLoading: isLoadingServices } = useQuery({
    queryKey: ['monitoring-services'],
    queryFn: api.monitoring.getServiceStatus,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Fetch active alerts
  const { data: alertsData, isLoading: isLoadingAlerts } = useQuery({
    queryKey: ['monitoring-alerts'],
    queryFn: api.monitoring.getActiveAlerts,
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  // Fetch system metrics
  const { data: systemMetrics } = useQuery({
    queryKey: ['monitoring-system'],
    queryFn: api.monitoring.getSystemMetrics,
    refetchInterval: 5000,
  });

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await api.monitoring.acknowledgeAlert(alertId);
      // Refetch alerts after acknowledging
      window.location.reload();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  // Calculate real-time metrics with real data
  const realTimeMetrics = realtimeData?.data?.summary ? [
    {
      title: "Active Processes",
      value: realtimeData.data.summary.active_processes.toString(),
      change: "+5",
      trend: "up" as const,
      icon: Activity,
      color: "text-primary"
    },
    {
      title: "Success Rate",
      value: `${realtimeData.data.summary.success_rate.toFixed(1)}%`,
      change: "+0.3%", 
      trend: "up" as const,
      icon: CheckCircle,
      color: "text-success"
    },
    {
      title: "Avg Response Time",
      value: `${realtimeData.data.summary.avg_response_time}ms`,
      change: "-120ms",
      trend: "down" as const,
      icon: Clock,
      color: "text-success"
    },
    {
      title: "Error Rate",
      value: `${realtimeData.data.summary.error_rate.toFixed(1)}%`,
      change: "-0.2%",
      trend: "down" as const,
      icon: AlertTriangle,
      color: "text-warning"
    }
  ] : [
    {
      title: "Active Processes",
      value: "23",
      change: "+5",
      trend: "up" as const,
      icon: Activity,
      color: "text-primary"
    },
    {
      title: "Success Rate",
      value: "99.2%",
      change: "+0.3%", 
      trend: "up" as const,
      icon: CheckCircle,
      color: "text-success"
    },
    {
      title: "Avg Response Time",
      value: "847ms",
      change: "-120ms",
      trend: "down" as const,
      icon: Clock,
      color: "text-success"
    },
    {
      title: "Error Rate",
      value: "0.8%",
      change: "-0.2%",
      trend: "down" as const,
      icon: AlertTriangle,
      color: "text-warning"
    }
  ];

  // Format service status from API
  const systemStatus = serviceData?.data?.services ? Object.entries(serviceData.data.services).map(([name, service]: [string, any]) => ({
    service: name,
    status: service.status,
    uptime: service.uptime || 'N/A',
    response: service.response || 'N/A'
  })) : [];

  // Use real alerts data
  const activeAlerts = alertsData?.data?.alerts || [];

  // Mock recent events (could be fetched from a real endpoint if available)
  const recentEvents = [
    {
      id: "1",
      type: "success",
      title: "Migration Completed Successfully", 
      description: "PostgreSQL to Snowflake migration for client_data",
      timestamp: "3 minutes ago",
      user: "admin@company.com"
    },
    {
      id: "2",
      type: "info",
      title: "Quality Scan Initiated",
      description: "Started automated quality check on uploaded dataset",
      timestamp: "12 minutes ago",
      user: "data.engineer@company.com"
    }
  ];

  if (isLoadingRealtime || isLoadingServices || isLoadingAlerts) {
    return (
      <div className="space-y-8">
        <div className="text-center">
          <p className="text-muted-foreground">Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Real-time Monitoring</h1>
          <p className="text-muted-foreground">
            Monitor system performance, active processes, and alerts across all platform services
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button variant="outline" onClick={() => refetchRealtime()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Real-time Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {realTimeMetrics.map((metric) => (
          <Card key={metric.title} className="metrics-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    {metric.title}
                  </p>
                  <p className="text-2xl font-bold">{metric.value}</p>
                  <div className="flex items-center mt-2">
                    <TrendingUp className={`h-4 w-4 mr-1 ${
                      metric.trend === 'up' ? 'text-success' : 'text-success rotate-180'
                    }`} />
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
        {/* System Status */}
        <div className="lg:col-span-2">
          <Card className="enterprise-card">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="h-5 w-5 mr-2" />
                System Status
              </CardTitle>
              <CardDescription>
                Real-time status of all platform services and components
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {systemStatus.map((service) => (
                  <div key={service.service} className="flex items-center justify-between p-4 rounded-lg border border-border/50 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${
                        service.status === 'operational' ? 'bg-success' :
                        service.status === 'degraded' ? 'bg-warning' : 'bg-muted-foreground'
                      }`} />
                      <div>
                        <p className="font-medium">{service.service}</p>
                        <p className="text-sm text-muted-foreground">
                          Uptime: {service.uptime} • Response: {service.response}
                        </p>
                      </div>
                    </div>
                    <Badge variant={
                      service.status === 'operational' ? 'default' :
                      service.status === 'degraded' ? 'secondary' : 'outline'
                    }>
                      {service.status}
                    </Badge>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-muted/30 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">Overall System Health</h4>
                  <span className={`text-lg font-bold ${serviceData?.data?.overall_health === 'healthy' ? 'text-success' : 'text-warning'}`}>
                    {serviceData?.data?.overall_health === 'healthy' ? '99.5%' : '97.8%'}
                  </span>
                </div>
                <Progress value={serviceData?.data?.overall_health === 'healthy' ? 99.5 : 97.8} className="h-3" />
                <p className="text-sm text-muted-foreground mt-2">
                  {systemStatus.filter(s => s.status === 'operational').length} of {systemStatus.length} services operational
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Activity Log */}
          <Card className="enterprise-card mt-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="h-5 w-5 mr-2" />
                Recent Activity
              </CardTitle>
              <CardDescription>
                Latest system events and user actions across the platform
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentEvents.map((event) => (
                  <div key={event.id} className="flex items-start space-x-4 p-3 rounded-lg border border-border/50">
                    <div className="flex-shrink-0 mt-0.5">
                      {event.type === 'success' && <CheckCircle className="h-5 w-5 text-success" />}
                      {event.type === 'info' && <Activity className="h-5 w-5 text-primary" />}
                      {event.type === 'warning' && <AlertTriangle className="h-5 w-5 text-warning" />}
                      {event.type === 'error' && <XCircle className="h-5 w-5 text-danger" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm">{event.title}</p>
                      <p className="text-sm text-muted-foreground">{event.description}</p>
                      <div className="flex items-center mt-2 space-x-4 text-xs text-muted-foreground">
                        <span>{event.timestamp}</span>
                        <span>•</span>
                        <span>{event.user}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts Panel */}
        <div>
          <Card className="enterprise-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center">
                  <Bell className="h-5 w-5 mr-2" />
                  Active Alerts
                </CardTitle>
                <Badge variant="secondary">{activeAlerts.length}</Badge>
              </div>
              <CardDescription>
                Current system alerts and notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {activeAlerts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="h-12 w-12 mx-auto mb-2 text-success" />
                  <p>No active alerts</p>
                </div>
              ) : (
                activeAlerts.map((alert) => (
                  <div key={alert.id} className={`p-4 rounded-lg border-l-4 ${
                    alert.severity === 'high' ? 'border-l-danger bg-danger/5' :
                    alert.severity === 'medium' ? 'border-l-warning bg-warning/5' :
                    'border-l-primary bg-primary/5'
                  }`}>
                    <div className="flex items-start justify-between mb-2">
                      <Badge variant={
                        alert.severity === 'high' ? 'destructive' :
                        alert.severity === 'medium' ? 'secondary' : 'outline'
                      }>
                        {alert.severity} priority
                      </Badge>
                    </div>
                    <h4 className="font-medium text-sm mb-1">{alert.title}</h4>
                    <p className="text-sm text-muted-foreground mb-2">{alert.description}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{alert.timestamp}</span>
                      <Button variant="outline" size="sm" onClick={() => handleAcknowledgeAlert(alert.id)}>
                        Acknowledge
                      </Button>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      Affected: {alert.affected}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Performance Stats */}
          <Card className="enterprise-card mt-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="h-5 w-5 mr-2" />
                Performance Stats
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>CPU Usage</span>
                    <span className={`font-medium ${
                      (systemMetrics?.data?.cpu?.usage_percent || 0) > 80 ? 'text-warning' : ''
                    }`}>
                      {systemMetrics?.data?.cpu?.usage_percent?.toFixed(0) || '68'}%
                    </span>
                  </div>
                  <Progress value={systemMetrics?.data?.cpu?.usage_percent || 68} />
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Memory Usage</span>
                    <span className={`font-medium ${
                      (systemMetrics?.data?.memory?.usage_percent || 0) > 80 ? 'text-warning' : ''
                    }`}>
                      {systemMetrics?.data?.memory?.usage_percent?.toFixed(0) || '74'}%
                    </span>
                  </div>
                  <Progress value={systemMetrics?.data?.memory?.usage_percent || 74} />
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Storage Usage</span>
                    <span className={`font-medium ${
                      (systemMetrics?.data?.disk?.usage_percent || 0) > 80 ? 'text-warning' : ''
                    }`}>
                      {systemMetrics?.data?.disk?.usage_percent?.toFixed(0) || '45'}%
                    </span>
                  </div>
                  <Progress value={systemMetrics?.data?.disk?.usage_percent || 45} />
                </div>

                <div className="pt-2 border-t border-border">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center">
                      <Users className="h-4 w-4 mr-2" />
                      Active Users
                    </span>
                    <span className="font-medium">{realtimeData?.data?.summary?.active_processes || '247'}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}