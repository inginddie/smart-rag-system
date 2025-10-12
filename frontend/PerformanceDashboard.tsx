import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Zap,
  RefreshCw,
} from 'lucide-react';

interface AgentMetrics {
  agent_name: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_duration_ms: number;
  p95_duration_ms?: number;
  p99_duration_ms?: number;
}

interface CircuitBreakerMetrics {
  state: 'closed' | 'open' | 'half_open';
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  rejected_calls: number;
}

interface PerformanceReport {
  global_metrics: {
    total_requests: number;
    success_rate: number;
    avg_duration_ms: number;
    throughput_per_second: number;
  };
  agent_metrics: Record<string, AgentMetrics>;
  slow_agents: AgentMetrics[];
  failing_agents: AgentMetrics[];
  circuit_breaker_status: Record<string, CircuitBreakerMetrics>;
}

export default function PerformanceDashboard() {
  const [report, setReport] = useState<PerformanceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchReport = async () => {
    try {
      const response = await fetch('/api/performance/report');
      const data = await response.json();
      
      if (data.status === 'success') {
        setReport(data.data);
        setError(null);
      } else {
        setError('Failed to fetch performance report');
      }
    } catch (err) {
      setError('Error connecting to API');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
    
    if (autoRefresh) {
      const interval = setInterval(fetchReport, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const resetCircuitBreaker = async (agentName: string) => {
    try {
      await fetch(`/api/performance/circuit-breakers/${agentName}/reset`, {
        method: 'POST',
      });
      fetchReport(); // Refresh data
    } catch (err) {
      console.error('Error resetting circuit breaker:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin h-8 w-8 text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!report) return null;

  const { global_metrics, agent_metrics, slow_agents, failing_agents } = report;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Performance Dashboard</h1>
          <p className="text-gray-500">Real-time system metrics and agent health</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className="mr-2 h-4 w-4" />
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>
          <Button onClick={fetchReport} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Global Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {global_metrics.total_requests.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(global_metrics.success_rate * 100).toFixed(1)}%
            </div>
            <Badge
              variant={global_metrics.success_rate > 0.95 ? 'default' : 'destructive'}
              className="mt-2"
            >
              {global_metrics.success_rate > 0.95 ? 'Healthy' : 'Degraded'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {global_metrics.avg_duration_ms.toFixed(0)}ms
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Throughput</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {global_metrics.throughput_per_second.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">requests/sec</p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {(slow_agents.length > 0 || failing_agents.length > 0) && (
        <div className="space-y-2">
          {slow_agents.length > 0 && (
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                <strong>{slow_agents.length} slow agent(s) detected:</strong>{' '}
                {slow_agents.map((a) => a.agent_name).join(', ')}
              </AlertDescription>
            </Alert>
          )}
          {failing_agents.length > 0 && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>{failing_agents.length} failing agent(s) detected:</strong>{' '}
                {failing_agents.map((a) => a.agent_name).join(', ')}
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      {/* Agent Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Performance</CardTitle>
          <CardDescription>Detailed metrics for each agent</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Agent</th>
                  <th className="text-right p-2">Requests</th>
                  <th className="text-right p-2">Success Rate</th>
                  <th className="text-right p-2">Avg Latency</th>
                  <th className="text-right p-2">P95</th>
                  <th className="text-right p-2">P99</th>
                  <th className="text-center p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {Object.values(agent_metrics).map((agent) => (
                  <tr key={agent.agent_name} className="border-b hover:bg-gray-50">
                    <td className="p-2 font-medium">{agent.agent_name}</td>
                    <td className="text-right p-2">{agent.total_requests}</td>
                    <td className="text-right p-2">
                      <span
                        className={
                          agent.success_rate > 0.95
                            ? 'text-green-600'
                            : agent.success_rate > 0.8
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }
                      >
                        {(agent.success_rate * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="text-right p-2">
                      {agent.avg_duration_ms.toFixed(0)}ms
                    </td>
                    <td className="text-right p-2">
                      {agent.p95_duration_ms?.toFixed(0) || '-'}ms
                    </td>
                    <td className="text-right p-2">
                      {agent.p99_duration_ms?.toFixed(0) || '-'}ms
                    </td>
                    <td className="text-center p-2">
                      {agent.success_rate > 0.95 ? (
                        <Badge variant="default">
                          <CheckCircle className="mr-1 h-3 w-3" />
                          Healthy
                        </Badge>
                      ) : agent.success_rate > 0.8 ? (
                        <Badge variant="secondary">
                          <AlertTriangle className="mr-1 h-3 w-3" />
                          Degraded
                        </Badge>
                      ) : (
                        <Badge variant="destructive">
                          <AlertTriangle className="mr-1 h-3 w-3" />
                          Failing
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Circuit Breakers */}
      <Card>
        <CardHeader>
          <CardTitle>Circuit Breakers</CardTitle>
          <CardDescription>Protection status for each agent</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(report.circuit_breaker_status || {}).map(
              ([agentName, metrics]) => (
                <Card key={agentName}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm">{agentName}</CardTitle>
                      <Badge
                        variant={
                          metrics.state === 'closed'
                            ? 'default'
                            : metrics.state === 'open'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {metrics.state.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Success:</span>
                      <span className="font-medium">{metrics.successful_calls}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Failed:</span>
                      <span className="font-medium text-red-600">
                        {metrics.failed_calls}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Rejected:</span>
                      <span className="font-medium text-orange-600">
                        {metrics.rejected_calls}
                      </span>
                    </div>
                    {metrics.state !== 'closed' && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-full mt-2"
                        onClick={() => resetCircuitBreaker(agentName)}
                      >
                        <Zap className="mr-2 h-3 w-3" />
                        Reset
                      </Button>
                    )}
                  </CardContent>
                </Card>
              )
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
