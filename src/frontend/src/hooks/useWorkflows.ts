/**
 * Hook for managing workflows
 */

import { useState, useEffect, useCallback } from 'react';
import { orchestratorService } from '../services';
import type { Workflow, WorkflowRequest, WorkflowListResponse } from '../types/api.types';

export function useWorkflows(pollInterval = 5000) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkflows = useCallback(async () => {
    try {
      const response: WorkflowListResponse = await orchestratorService.listWorkflows();
      setWorkflows(response.workflows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch workflows');
    } finally {
      setLoading(false);
    }
  }, []);

  const startWorkflow = useCallback(async (request: WorkflowRequest) => {
    setLoading(true);
    try {
      const response = await orchestratorService.startWorkflow(request);
      await fetchWorkflows();
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start workflow');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchWorkflows]);

  const cancelWorkflow = useCallback(async (workflowId: string) => {
    try {
      await orchestratorService.cancelWorkflow(workflowId);
      await fetchWorkflows();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel workflow');
      throw err;
    }
  }, [fetchWorkflows]);

  useEffect(() => {
    fetchWorkflows();
    const interval = setInterval(fetchWorkflows, pollInterval);
    return () => clearInterval(interval);
  }, [fetchWorkflows, pollInterval]);

  return {
    workflows,
    loading,
    error,
    startWorkflow,
    cancelWorkflow,
    refresh: fetchWorkflows,
  };
}
