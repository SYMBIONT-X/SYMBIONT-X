/**
 * Human-in-the-Loop Service
 */

import { api } from './api';

export interface Approval {
  approval_id: string;
  workflow_id: string;
  approval_type: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  title: string;
  description: string;
  vulnerability_ids: string[];
  priority: string;
  risk_summary: string;
  recommended_action: string;
  requested_by: string;
  requested_at: string;
  expires_at: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_comment: string | null;
}

export interface Comment {
  comment_id: string;
  target_type: string;
  target_id: string;
  author: string;
  content: string;
  created_at: string;
  edited_at: string | null;
  mentions: string[];
}

export interface AuditEntry {
  entry_id: string;
  timestamp: string;
  action: string;
  actor: string;
  workflow_id: string | null;
  vulnerability_id: string | null;
  approval_id: string | null;
  details: Record<string, unknown>;
  success: boolean;
  error_message: string | null;
}

export const hitlService = {
  // Approvals
  async listApprovals(params?: {
    status?: string;
    workflow_id?: string;
    priority?: string;
  }): Promise<{ total: number; approvals: Approval[] }> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.workflow_id) query.set('workflow_id', params.workflow_id);
    if (params?.priority) query.set('priority', params.priority);
    
    const queryString = query.toString();
    return api.get('orchestrator', `/hitl/approvals${queryString ? `?${queryString}` : ''}`);
  },

  async getPendingApprovals(): Promise<{ total: number; approvals: Approval[] }> {
    return api.get('orchestrator', '/hitl/approvals/pending');
  },

  async getApproval(approvalId: string): Promise<{ approval: Approval; comments: Comment[] }> {
    return api.get('orchestrator', `/hitl/approvals/${approvalId}`);
  },

  async decideApproval(
    approvalId: string,
    decision: { approved: boolean; resolver: string; comment?: string }
  ): Promise<{ approval_id: string; status: string; message: string }> {
    return api.post('orchestrator', `/hitl/approvals/${approvalId}/decide`, decision);
  },

  // Comments
  async addComment(request: {
    target_type: string;
    target_id: string;
    author: string;
    content: string;
    mentions?: string[];
  }): Promise<{ comment_id: string; comment: Comment }> {
    return api.post('orchestrator', '/hitl/comments', request);
  },

  async getComments(targetId: string): Promise<{ total: number; comments: Comment[] }> {
    return api.get('orchestrator', `/hitl/comments/${targetId}`);
  },

  // Audit Log
  async getAuditLog(params?: {
    workflow_id?: string;
    vulnerability_id?: string;
    action?: string;
    limit?: number;
  }): Promise<{ total: number; entries: AuditEntry[] }> {
    const query = new URLSearchParams();
    if (params?.workflow_id) query.set('workflow_id', params.workflow_id);
    if (params?.vulnerability_id) query.set('vulnerability_id', params.vulnerability_id);
    if (params?.action) query.set('action', params.action);
    if (params?.limit) query.set('limit', params.limit.toString());
    
    const queryString = query.toString();
    return api.get('orchestrator', `/hitl/audit${queryString ? `?${queryString}` : ''}`);
  },

  async getWorkflowTimeline(workflowId: string): Promise<{
    workflow_id: string;
    timeline: AuditEntry[];
    comments: Comment[];
  }> {
    return api.get('orchestrator', `/hitl/audit/workflow/${workflowId}/timeline`);
  },

  async getAuditStats(): Promise<{
    total_entries: number;
    total_comments: number;
    by_action: Record<string, number>;
  }> {
    return api.get('orchestrator', '/hitl/audit/stats');
  },
};
