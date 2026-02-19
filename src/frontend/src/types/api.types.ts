/**
 * API Types for SYMBIONT-X
 */

// ============ Common ============

export interface HealthResponse {
  status: string;
  agent: string;
  version: string;
  timestamp: string;
  agents?: Record<string, string>;
  scanners?: Record<string, boolean>;
  ai_enabled?: boolean;
  github_enabled?: boolean;
  templates_count?: number;
}

// ============ Orchestrator ============

export interface AgentStatusResponse {
  agents: Record<string, {
    status: string;
    url: string;
    version: string | null;
    last_check: string | null;
  }>;
  all_healthy: boolean;
}

export interface WorkflowStep {
  step_id: string;
  action: string;
  status: string;
  agent: string | null;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface Workflow {
  workflow_id: string;
  repository: string;
  branch: string;
  status: WorkflowStatus;
  current_step: string | null;
  steps: WorkflowStep[];
  scan_id: string | null;
  assessment_id: string | null;
  remediation_ids: string[];
  total_vulnerabilities: number;
  critical_count: number;
  high_count: number;
  auto_remediated: number;
  awaiting_approval: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  triggered_by: string;
  metadata: Record<string, unknown>;
}

export type WorkflowStatus =
  | 'pending'
  | 'scanning'
  | 'assessing'
  | 'awaiting_approval'
  | 'remediating'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface WorkflowRequest {
  repository: string;
  branch?: string;
  scan_types?: string[];
  auto_remediate?: boolean;
  notify?: boolean;
}

export interface WorkflowResponse {
  workflow_id: string;
  status: WorkflowStatus;
  message: string;
  workflow: Workflow | null;
}

export interface WorkflowListResponse {
  total: number;
  workflows: Workflow[];
}

// ============ Scanner ============

export interface ScannerInfo {
  name: string;
  type: string;
  available: boolean;
  description: string;
}

export interface ScanRequest {
  repository: string;
  branch?: string;
  commit_sha?: string;
  scan_types?: string[];
  target_path?: string;
}

export interface Vulnerability {
  id: string;
  cve_id: string | null;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'unknown';
  cvss_score: number | null;
  package_name: string | null;
  package_version: string | null;
  fixed_version: string | null;
  file_path: string | null;
  line_number: number | null;
  source: string;
  repository: string;
  branch: string;
  detected_at: string;
}

export interface ScanResult {
  scan_id: string;
  scan_type: string;
  repository: string;
  branch: string;
  success: boolean;
  vulnerabilities: Vulnerability[];
  total_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  started_at: string;
  completed_at: string | null;
  scan_duration_seconds: number | null;
}

export interface ScanResponse {
  scan_id: string;
  status: 'started' | 'running' | 'completed' | 'failed';
  message: string;
  results?: ScanResult[];
}

// ============ Assessment ============

export interface BusinessContext {
  repository: string;
  service_name?: string;
  service_type: string;
  is_public_facing: boolean;
  is_internet_exposed: boolean;
  data_sensitivity: string;
  handles_pii: boolean;
  handles_financial_data: boolean;
  handles_health_data: boolean;
  business_criticality: number;
  revenue_impact: boolean;
  customer_facing: boolean;
  compliance_requirements: string[];
  dependent_services: string[];
  dependency_count: number;
}

export interface RiskScore {
  cvss_score: number;
  exploitability_score: number;
  business_impact_score: number;
  data_sensitivity_score: number;
  total_score: number;
  priority: Priority;
  factors: string[];
  ai_analysis: string | null;
}

export type Priority = 'P0' | 'P1' | 'P2' | 'P3' | 'P4';

export interface RiskAssessment {
  vulnerability_id: string;
  cve_id: string | null;
  title: string;
  severity: string;
  cvss_score: number | null;
  business_context: BusinessContext | null;
  risk_score: RiskScore;
  remediation_urgency: string;
  recommended_action: string;
  estimated_effort: string | null;
  assessed_at: string;
  assessed_by: string;
}

export interface AssessmentRequest {
  vulnerabilities: Record<string, unknown>[];
  repository: string;
  business_context?: BusinessContext;
  use_ai_analysis?: boolean;
}

export interface AssessmentResponse {
  assessment_id: string;
  repository: string;
  total_assessed: number;
  assessments: RiskAssessment[];
  summary: Record<string, number>;
  assessed_at: string;
}

// ============ Remediation ============

export interface FileChange {
  file_path: string;
  action: 'create' | 'modify' | 'delete';
  original_content: string | null;
  new_content: string | null;
  diff: string | null;
}

export interface GeneratedFix {
  fix_id: string;
  vulnerability_id: string;
  cve_id: string | null;
  fix_type: string;
  title: string;
  description: string;
  changes: FileChange[];
  confidence: 'high' | 'medium' | 'low';
  template_used: string | null;
  ai_generated: boolean;
  test_commands: string[];
  rollback_steps: string[];
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface PullRequestInfo {
  pr_number: number;
  pr_url: string;
  branch_name: string;
  title: string;
  status: string;
  created_at: string;
  merged_at: string | null;
}

export interface RemediationRequest {
  vulnerability: Record<string, unknown>;
  repository: string;
  branch?: string;
  priority?: string;
  auto_create_pr?: boolean;
  require_approval?: boolean;
}

export interface RemediationResponse {
  remediation_id: string;
  vulnerability_id: string;
  status: string;
  fix: GeneratedFix | null;
  pr_info: PullRequestInfo | null;
  message: string;
}

export interface BatchRemediationRequest {
  vulnerabilities: Record<string, unknown>[];
  repository: string;
  branch?: string;
  auto_create_pr?: boolean;
  priority_filter?: string[];
}

export interface BatchRemediationResponse {
  batch_id: string;
  total_vulnerabilities: number;
  fixes_generated: number;
  prs_created: number;
  results: RemediationResponse[];
}

export interface FixTemplate {
  id: string;
  name: string;
  description: string;
  fix_type: string;
  confidence: string;
  applicable_to: string[];
}
