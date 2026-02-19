/**
 * Auto-Remediation Agent Service
 */

import { api } from './api';
import type {
  RemediationRequest,
  RemediationResponse,
  BatchRemediationRequest,
  BatchRemediationResponse,
  FixTemplate,
} from '../types/api.types';

export const remediationService = {
  /**
   * Get remediation agent health
   */
  async getHealth(): Promise<{
    status: string;
    agent: string;
    version: string;
    github_enabled: boolean;
    ai_enabled: boolean;
    templates_count: number;
    timestamp: string;
  }> {
    return api.get('remediation', '/health');
  },

  /**
   * Remediate single vulnerability
   */
  async remediate(request: RemediationRequest): Promise<RemediationResponse> {
    return api.post('remediation', '/remediate', request);
  },

  /**
   * Remediate batch of vulnerabilities
   */
  async remediateBatch(request: BatchRemediationRequest): Promise<BatchRemediationResponse> {
    return api.post('remediation', '/remediate/batch', request);
  },

  /**
   * Preview fix without creating PR
   */
  async previewFix(request: RemediationRequest): Promise<{
    fix: unknown;
    preview_only: boolean;
    message: string;
  }> {
    return api.post('remediation', '/preview', request);
  },

  /**
   * Get remediation status
   */
  async getRemediation(remediationId: string): Promise<RemediationResponse> {
    return api.get('remediation', `/remediation/${remediationId}`);
  },

  /**
   * List available templates
   */
  async getTemplates(): Promise<{ total: number; templates: FixTemplate[] }> {
    return api.get('remediation', '/templates');
  },

  /**
   * Get template by ID
   */
  async getTemplate(templateId: string): Promise<FixTemplate> {
    return api.get('remediation', `/templates/${templateId}`);
  },

  /**
   * Get statistics
   */
  async getStats(): Promise<{
    fix_generator: { total_templates: number; by_type: Record<string, number>; ai_enabled: boolean };
    remediations: { total: number; by_status: Record<string, number> };
    github: { enabled: boolean };
  }> {
    return api.get('remediation', '/stats');
  },
};
