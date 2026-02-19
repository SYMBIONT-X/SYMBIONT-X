/**
 * Base API client for SYMBIONT-X agents
 */

const API_URLS = {
  orchestrator: import.meta.env.VITE_ORCHESTRATOR_URL || 'http://localhost:8000',
  scanner: import.meta.env.VITE_SCANNER_URL || 'http://localhost:8001',
  assessment: import.meta.env.VITE_ASSESSMENT_URL || 'http://localhost:8002',
  remediation: import.meta.env.VITE_REMEDIATION_URL || 'http://localhost:8003',
};

export type AgentType = keyof typeof API_URLS;

class ApiClient {
  private async request<T>(
    agent: AgentType,
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const baseUrl = API_URLS[agent];
    const url = `${baseUrl}${endpoint}`;

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error(`API Error [${agent}${endpoint}]:`, error);
      throw error;
    }
  }

  async get<T>(agent: AgentType, endpoint: string): Promise<T> {
    return this.request<T>(agent, endpoint, { method: 'GET' });
  }

  async post<T>(agent: AgentType, endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(agent, endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

export const api = new ApiClient();
export { API_URLS };
