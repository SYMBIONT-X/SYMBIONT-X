/**
 * Risk Assessment Agent Service
 */

import { api } from './api';
import type {
  AssessmentRequest,
  AssessmentResponse,
  RiskAssessment,
  BusinessContext,
} from '../types/api.types';

export const assessmentService = {
  /**
   * Get assessment agent health
   */
  async getHealth(): Promise<{
    status: string;
    agent: string;
    version: string;
    ai_enabled: boolean;
    timestamp: string;
  }> {
    return api.get('assessment', '/health');
  },

  /**
   * Assess vulnerabilities
   */
  async assessVulnerabilities(request: AssessmentRequest): Promise<AssessmentResponse> {
    return api.post('assessment', '/assess', request);
  },

  /**
   * Assess single vulnerability
   */
  async assessSingle(request: {
    vulnerability: Record<string, unknown>;
    repository: string;
    business_context?: BusinessContext;
    use_ai_analysis?: boolean;
  }): Promise<RiskAssessment> {
    return api.post('assessment', '/assess/single', request);
  },

  /**
   * Get assessment by ID
   */
  async getAssessment(assessmentId: string): Promise<AssessmentResponse> {
    return api.get('assessment', `/assessment/${assessmentId}`);
  },

  /**
   * Register business context
   */
  async registerContext(context: BusinessContext): Promise<BusinessContext> {
    return api.post('assessment', '/context', context);
  },

  /**
   * Get business context for repository
   */
  async getContext(repository: string): Promise<BusinessContext> {
    return api.get('assessment', `/context/${repository}`);
  },

  /**
   * Get priority definitions
   */
  async getPriorities(): Promise<{
    priorities: Array<{
      level: string;
      name: string;
      description: string;
      sla: string;
      threshold: string;
    }>;
    weights: Record<string, number>;
  }> {
    return api.get('assessment', '/priorities');
  },
};
