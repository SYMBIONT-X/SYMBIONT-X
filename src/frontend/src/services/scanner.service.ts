/**
 * Security Scanner Agent Service
 */

import { api } from './api';
import type { ScanRequest, ScanResponse, ScannerInfo } from '../types/api.types';

export const scannerService = {
  /**
   * Get scanner health
   */
  async getHealth(): Promise<{
    status: string;
    agent: string;
    version: string;
    scanners: Record<string, boolean>;
    timestamp: string;
  }> {
    return api.get('scanner', '/health');
  },

  /**
   * List available scanners
   */
  async getScanners(): Promise<{ scanners: ScannerInfo[] }> {
    return api.get('scanner', '/scanners');
  },

  /**
   * Trigger a scan
   */
  async triggerScan(request: ScanRequest): Promise<ScanResponse> {
    return api.post('scanner', '/scan', request);
  },

  /**
   * Get scan results
   */
  async getScanResults(scanId: string): Promise<ScanResponse> {
    return api.get('scanner', `/scan/${scanId}`);
  },

  /**
   * Lookup CVE details
   */
  async lookupCVE(cveId: string): Promise<unknown> {
    return api.get('scanner', `/cve/${cveId}`);
  },
};
