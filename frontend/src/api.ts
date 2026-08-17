import axios from 'axios';

// Works whether served from localhost or a remote server
const BASE = `${window.location.origin}/api`;

export const api = axios.create({ baseURL: BASE });

export interface Engagement {
  id: number;
  name: string;
  entity_name?: string;
  period?: string;
  currency: string;
  overall_materiality?: number;
  performance_materiality?: number;
  trivial_threshold?: number;
  status: string;
  created_at: string;
}

export interface TBAccount {
  id: number;
  account_code: string;
  account_name: string;
  sub_account?: string;
  account_type_raw: string;
  beginning_balance: number;
  period_activity: number;
  ending_balance: number;
  is_zero: boolean;
  is_unusual: boolean;
  unusual_reason?: string;
}

export interface AccountMapping {
  account_code: string;
  account_name: string;
  account_type_raw: string;
  beginning_balance: number;
  ending_balance: number;
  fs_statement: string;
  fs_category: string;
  fs_line_item: string;
  lead_line: string;
  confidence: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  reason: string;
  ifrs_reference?: string;
  source: string;
  user_approved: number;
  user_modified: number;
  user_note?: string;
  is_unusual?: boolean;
  unusual_reason?: string;
}

export interface ValidationResult {
  check_name: string;
  result: 'PASS' | 'WARNING' | 'ERROR';
  expected?: string;
  actual?: string;
  difference?: string;
  severity: string;
  explanation: string;
}

// Engagements
export const getEngagements = () => api.get<Engagement[]>('/engagements').then(r => r.data);
export const createEngagement = (data: any) => api.post<{ id: number }>('/engagements', data).then(r => r.data);
export const getEngagement = (id: number) => api.get<Engagement>(`/engagements/${id}`).then(r => r.data);
export const updateEngagement = (id: number, data: any) => api.patch(`/engagements/${id}`, data).then(r => r.data);

// Files
export const uploadFile = (eid: number, file: File, fileType: string) => {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('file_type', fileType);
  return api.post(`/engagements/${eid}/upload`, fd).then(r => r.data);
};
export const getFiles = (eid: number) => api.get(`/engagements/${eid}/files`).then(r => r.data);

// Analysis
export const analyzeTB = (eid: number) => api.post(`/engagements/${eid}/analyze-tb`).then(r => r.data);
export const getAccounts = (eid: number) => api.get<TBAccount[]>(`/engagements/${eid}/accounts`).then(r => r.data);
export const analyzeTemplate = (eid: number, templateType: string) =>
  api.post(`/engagements/${eid}/analyze-template?template_type=${templateType}`).then(r => r.data);

// Classification
export const classify = (eid: number, useAI: boolean = true) =>
  api.post(`/engagements/${eid}/classify?use_ai=${useAI}`).then(r => r.data);
export const getMappings = (eid: number) => api.get<AccountMapping[]>(`/engagements/${eid}/mappings`).then(r => r.data);
export const updateMapping = (eid: number, code: string, data: any) =>
  api.patch(`/engagements/${eid}/mappings/${code}`, data).then(r => r.data);
export const approveMapping = (eid: number, code: string) =>
  api.post(`/engagements/${eid}/mappings/${code}/approve`).then(r => r.data);
export const bulkApprove = (eid: number, codes: string[]) =>
  api.post(`/engagements/${eid}/mappings/bulk-approve`, { account_codes: codes }).then(r => r.data);

// Validation
export const validate = (eid: number) => api.post(`/engagements/${eid}/validate`).then(r => r.data);
export const getAggregatedBalances = (eid: number) =>
  api.get(`/engagements/${eid}/aggregated-balances`).then(r => r.data);

// Generate & Download
export const generate = (eid: number, audit: boolean, fs: boolean) =>
  api.post(`/engagements/${eid}/generate?generate_audit_file=${audit}&generate_fs_draft=${fs}`).then(r => r.data);

export const downloadUrl = (eid: number, type: string) => `${BASE}/engagements/${eid}/download/${type}`;
export const downloadMappingUrl = (eid: number) => `${BASE}/engagements/${eid}/download-mapping-report`;
export const downloadAuditTrailUrl = (eid: number) => `${BASE}/engagements/${eid}/download-audit-trail`;
export const downloadValidationUrl = (eid: number) => `${BASE}/engagements/${eid}/download-validation-report`;
