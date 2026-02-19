/**
 * Orchestrator Agent Service
 */

import { api } from './api';
import type {
  HealthResponse,
  AgentStatusResponse,
  
  WorkflowRequest,
  WorkflowResponse,
  WorkflowListResponse,
} from '../types/api.types';

export const orchestratorService = {
  /**
   * Get orchestrator health and agent statuses
   */
  async getHealth(): Promise<HealthResponse> {
    return api.get('orchestrator', '/health');
  },

  /**
   * Get detailed agent status
   */
  async getAgents(): Promise<AgentStatusResponse> {
    return api.get('orchestrator', '/agents');
  },

  /**
   * Start a new workflow
   */
  async startWorkflow(request: WorkflowRequest): Promise<WorkflowResponse> {
    return api.post('orchestrator', '/workflow', request);
  },

  /**
   * Get workflow by ID
   */
  async getWorkflow(workflowId: string): Promise<WorkflowResponse> {
    return api.get('orchestrator', `/workflow/${workflowId}`);
  },

  /**
   * List all workflows
   */
  async listWorkflows(params?: {
    status?: string;
    repository?: string;
    limit?: number;
  }): Promise<WorkflowListResponse> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.repository) query.set('repository', params.repository);
    if (params?.limit) query.set('limit', params.limit.toString());
    
    const queryString = query.toString();
    return api.get('orchestrator', `/workflows${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get pending approvals
   */
  async getPendingApprovals(): Promise<WorkflowListResponse> {
    return api.get('orchestrator', '/approvals');
  },

  /**
   * Approve or reject remediation
   */
  async approveRemediation(request: {
    workflow_id: string;
    vulnerability_ids: string[];
    approved: boolean;
    approver: string;
    comment?: string;
  }): Promise<WorkflowResponse> {
    return api.post('orchestrator', '/approve', request);
  },

  /**
   * Cancel a workflow
   */
  async cancelWorkflow(workflowId: string): Promise<WorkflowResponse> {
    return api.post('orchestrator', `/workflow/${workflowId}/cancel`);
  },

  /**
   * Get statistics
   */
  async getStats(): Promise<{
    workflows: { total: number; by_status: Record<string, number> };
    agents: Record<string, unknown>;
  }> {
    return api.get('orchestrator', '/stats');
  },
};
