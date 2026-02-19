/**
 * Hook for monitoring agent status
 */

import { useState, useEffect, useCallback } from 'react';
import { orchestratorService } from '../services';
import type { AgentStatusResponse } from '../types/api.types';

interface AgentStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  url: string;
  version: string | null;
  lastCheck: string | null;
}

export function useAgentStatus(pollInterval = 10000) {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [allHealthy, setAllHealthy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const response: AgentStatusResponse = await orchestratorService.getAgents();
      
      const agentList: AgentStatus[] = Object.entries(response.agents).map(
        ([name, info]) => ({
          name,
          status: info.status as 'healthy' | 'unhealthy' | 'unknown',
          url: info.url,
          version: info.version,
          lastCheck: info.last_check,
        })
      );

      setAgents(agentList);
      setAllHealthy(response.all_healthy);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, pollInterval);
    return () => clearInterval(interval);
  }, [fetchStatus, pollInterval]);

  return { agents, allHealthy, loading, error, refresh: fetchStatus };
}
