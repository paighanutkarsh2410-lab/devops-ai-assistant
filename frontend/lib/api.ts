import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auth API
export const authAPI = {
  signup: (data: { email: string; password: string; full_name?: string; company?: string }) =>
    api.post('/auth/signup', data),

  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),

  getCurrentUser: () =>
    api.get('/auth/me'),
};

// Incidents API
export const incidentsAPI = {
  getAll: (params?: { status?: string; skip?: number; limit?: number }) =>
    api.get('/incidents/', { params }),

  getOne: (id: string) =>
    api.get(`/incidents/${id}`),

  create: (data: { title: string; description?: string; severity: string; service_name?: string }) =>
    api.post('/incidents/', data),

  update: (id: string, data: { status?: string; root_cause?: string; solution?: string; resolved_at?: string }) =>
    api.patch(`/incidents/${id}`, data),

  delete: (id: string) =>
    api.delete(`/incidents/${id}`),
};

// Metrics API
export const metricsAPI = {
  getAll: (params?: { service_name?: string; metric_name?: string; hours?: number; limit?: number }) =>
    api.get('/metrics/', { params }),

  getAggregations: (params: { service_name: string; metric_name: string; hours?: number }) =>
    api.get('/metrics/aggregations', { params }),
};

// Logs API
export const logsAPI = {
  getAll: (params?: { service_name?: string; level?: string; hours?: number }) =>
    api.get('/logs/', { params }),

  getErrors: (params?: { service_name?: string; hours?: number }) =>
    api.get('/logs/errors', { params }),

  getPatterns: (params?: { service_name?: string; hours?: number }) =>
    api.get('/logs/patterns', { params }),
};

// Deployments API
export const deploymentsAPI = {
  getAll: (params?: { service_name?: string }) =>
    api.get('/deployments/', { params }),

  getRecent: (params?: { hours?: number }) =>
    api.get('/deployments/recent', { params }),

  create: (data: { service_name: string; version: string; commit_hash?: string; deployed_by?: string; description?: string }) =>
    api.post('/deployments/', data),
};

// Approvals API
export const approvalsAPI = {
  getAll: (params?: { status?: string; limit?: number }) =>
    api.get('/approvals/', { params }),

  getOne: (id: string) =>
    api.get(`/approvals/${id}`),

  approve: (id: string) =>
    api.post(`/approvals/${id}/approve`, {}),

  reject: (id: string) =>
    api.post(`/approvals/${id}/reject`, {}),
};

// Audit API
export const auditAPI = {
  getActions: (params?: { status?: string; action_name?: string; limit?: number; skip?: number }) =>
    api.get('/audit/actions', { params }),

  getAction: (id: string) =>
    api.get(`/audit/actions/${id}`),

  getIncidentActions: (incidentId: string) =>
    api.get(`/audit/incidents/${incidentId}/actions`),

  getStats: () =>
    api.get('/audit/stats'),
};

// Learning API
export const learningAPI = {
  getPatterns: (params?: { trending?: string; limit?: number }) =>
    api.get('/learning/patterns', { params }),

  getStats: () =>
    api.get('/learning/stats'),

  getOutcomeStats: () =>
    api.get('/learning/outcomes/stats'),

  recommend: (incidentId: string) =>
    api.post('/learning/recommend', { incident_id: incidentId }),

  getLearningData: (params?: { pattern_type?: string; limit?: number }) =>
    api.get('/learning/data', { params }),

  getWeeklyReport: () =>
    api.get('/reports/learning/weekly'),

  getMonthlyReport: () =>
    api.get('/reports/learning/monthly'),

  getInsights: () =>
    api.get('/reports/learning/insights'),
};

// Predictions API
export const predictionsAPI = {
  getAlerts: (params?: { severity?: string; prevented?: boolean; limit?: number }) =>
    api.get('/alerts/predictive', { params }),

  getAlertStats: () =>
    api.get('/alerts/predictive/stats'),

  preventAlert: (id: string, actionTaken: string) =>
    api.post(`/alerts/predictive/${id}/prevent`, { action_taken: actionTaken }),

  getForecasts: (params?: { service_name?: string; metric_name?: string; limit?: number }) =>
    api.get('/predictions/metrics', { params }),

  getCapacityPlans: (params?: { status?: string; limit?: number }) =>
    api.get('/predictions/capacity', { params }),

  getCostForecast: () =>
    api.get('/predictions/costs/forecast'),

  getCurrentCosts: () =>
    api.get('/predictions/costs/current'),

  getCostOptimizations: () =>
    api.get('/predictions/costs/optimization'),

  getTrends: (params?: { service_name?: string; limit?: number }) =>
    api.get('/predictions/trends', { params }),
};

// Alerts API
export const alertsAPI = {
  getAll: (params?: { acknowledged?: boolean; resolved?: boolean; severity?: string; limit?: number }) =>
    api.get('/alerts/', { params }),

  update: (id: string, data: { acknowledged?: boolean; resolved?: boolean }) =>
    api.patch(`/alerts/${id}`, data),
};

// Reports API
export const reportsAPI = {
  postmortem: (incidentId: string) =>
    api.get(`/reports/incident/${incidentId}/postmortem`),
  weekly: () => api.get('/reports/weekly'),
  monthly: () => api.get('/reports/monthly'),
  executive: () => api.get('/reports/executive'),
};

// Preferences API
export const preferencesAPI = {
  getNotifications: () => api.get('/preferences/notifications'),
  updateNotifications: (prefs: unknown[]) =>
    api.put('/preferences/notifications', prefs),
  testNotification: () => api.post('/preferences/notifications/test'),
};

// Comments API
export const commentsAPI = {
  getAll: (incidentId: string) =>
    api.get(`/incidents/${incidentId}/comments`),
  create: (incidentId: string, text: string) =>
    api.post(`/incidents/${incidentId}/comments`, { comment_text: text }),
  update: (commentId: string, text: string) =>
    api.put(`/comments/${commentId}`, { comment_text: text }),
  delete: (commentId: string) =>
    api.delete(`/comments/${commentId}`),
};

// Analytics API
export const analyticsAPI = {
  dashboard: (days?: number) =>
    api.get('/analytics/dashboard', { params: { days } }),
  mttr: (params?: { days?: number; severity?: string; service_name?: string }) =>
    api.get('/analytics/mttr', { params }),
  mttd: (days?: number) =>
    api.get('/analytics/mttd', { params: { days } }),
  mtbf: (serviceName: string) =>
    api.get(`/analytics/mtbf/${serviceName}`),
  frequency: (days?: number) =>
    api.get('/analytics/frequency', { params: { days } }),
  rootCauses: () =>
    api.get('/analytics/root-causes'),
  reliability: (serviceName?: string) =>
    api.get('/analytics/reliability', { params: { service_name: serviceName } }),
  effectiveness: () =>
    api.get('/analytics/effectiveness'),
  costImpact: (hourlyRate?: number) =>
    api.get('/analytics/cost-impact', { params: { hourly_rate: hourlyRate } }),
};

// Report Builder API
export const reportBuilderAPI = {
  getTemplates: (reportType?: string) =>
    api.get('/report-builder/templates', { params: { report_type: reportType } }),
  createTemplate: (data: { name: string; description?: string; report_type?: string; widgets: unknown[]; schedule?: string }) =>
    api.post('/report-builder/templates', data),
  getTemplate: (id: string) =>
    api.get(`/report-builder/templates/${id}`),
  updateTemplate: (id: string, data: Record<string, unknown>) =>
    api.patch(`/report-builder/templates/${id}`, data),
  deleteTemplate: (id: string) =>
    api.delete(`/report-builder/templates/${id}`),
  generateReport: (id: string, days?: number) =>
    api.post(`/report-builder/templates/${id}/generate`, null, { params: { days } }),
  getPresets: () =>
    api.get('/report-builder/presets'),
};

// Trends API
export const trendsAPI = {
  summary: (days?: number) =>
    api.get('/trends/summary', { params: { days } }),
  severity: (days?: number) =>
    api.get('/trends/severity', { params: { days } }),
  services: (days?: number) =>
    api.get('/trends/services', { params: { days } }),
  resolution: (days?: number) =>
    api.get('/trends/resolution', { params: { days } }),
  anomalies: (days?: number) =>
    api.get('/trends/anomalies', { params: { days } }),
};

// SLA API
export const slaAPI = {
  getConfigs: () =>
    api.get('/sla/configs'),
  createConfig: (data: { service_name: string; target_uptime?: number; max_mttr_minutes?: number; max_incidents_per_month?: number | null }) =>
    api.post('/sla/configs', data),
  getStatus: (days?: number) =>
    api.get('/sla/status', { params: { days } }),
  getServiceStatus: (serviceName: string, days?: number) =>
    api.get(`/sla/status/${serviceName}`, { params: { days } }),
};

// Cost API
export const costsAPI = {
  roi: (params?: { days?: number; hourly_rate?: number }) =>
    api.get('/costs/roi', { params }),
  byService: (days?: number) =>
    api.get('/costs/by-service', { params: { days } }),
  trend: (days?: number) =>
    api.get('/costs/trend', { params: { days } }),
  optimizations: (days?: number) =>
    api.get('/costs/optimizations', { params: { days } }),
};

// Search API
export const searchAPI = {
  search: (params: Record<string, string>) =>
    api.get('/incidents/search/results', { params }),
  suggestions: (query: string) =>
    api.get('/incidents/search/suggestions', { params: { q: query } }),
  export: (params: Record<string, string>) =>
    api.get('/incidents/export', { params }),
};

// Explanations API
export const explanationsAPI = {
  getDiagnosis: (incidentId: string) =>
    api.get(`/explanations/incidents/${incidentId}/explanation`),
  getRemediation: (incidentId: string) =>
    api.get(`/explanations/incidents/${incidentId}/remediation-explanation`),
  getDecisionAudit: (limit?: number) =>
    api.get('/explanations/audit/decisions', { params: { limit } }),
};

// Agent Intelligence API
export const agentIntelligenceAPI = {
  orchestrationStatus: () =>
    api.get('/agents/orchestration/status'),
  coordinateResponse: (incidentId: string) =>
    api.post(`/agents/orchestration/coordinate/${incidentId}`),
  listSpecialists: () =>
    api.get('/agents/specialists'),
  specialistAnalyze: (specialistId: string, incidentId: string) =>
    api.post(`/agents/specialists/${specialistId}/analyze/${incidentId}`),
  learningProgress: () =>
    api.get('/agents/learning/progress'),
  detectedPatterns: () =>
    api.get('/agents/patterns'),
  performance: () =>
    api.get('/agents/performance'),
};

// Custom Agents API
export const customAgentsAPI = {
  list: () =>
    api.get('/agents/custom'),
  create: (data: any) =>
    api.post('/agents/custom', data),
  update: (id: string, data: any) =>
    api.put(`/agents/custom/${id}`, data),
  delete: (id: string) =>
    api.delete(`/agents/custom/${id}`),
  test: (id: string) =>
    api.post(`/agents/custom/${id}/test`),
  templates: () =>
    api.get('/agents/custom/templates'),
  actionLibrary: () =>
    api.get('/agents/custom/actions/library'),
};

// Marketplace API
export const marketplaceAPI = {
  browse: (params?: { category?: string; search?: string; sort_by?: string }) =>
    api.get('/marketplace/items', { params }),
  getItem: (id: string) =>
    api.get(`/marketplace/items/${id}`),
  install: (id: string) =>
    api.post(`/marketplace/items/${id}/install`),
  rate: (id: string, data: { rating: number; comment?: string }) =>
    api.post(`/marketplace/items/${id}/rate`, data),
  publish: (data: any) =>
    api.post('/marketplace/items', data),
};

// Agent Status API
export const agentStatusAPI = {
  health: () =>
    api.get('/agents/health/status'),
  logs: (params?: { agent_name?: string; level?: string; limit?: number }) =>
    api.get('/agents/health/logs', { params }),
  versions: () =>
    api.get('/agents/versions'),
  docs: () =>
    api.get('/agents/docs'),
  rollback: (agentName: string) =>
    api.post(`/agents/${agentName}/rollback`),
};

// Compliance API
export const complianceAPI = {
  status: () =>
    api.get('/compliance/status'),
  auditLog: (params?: { actor?: string; action?: string; limit?: number }) =>
    api.get('/compliance/audit-log', { params }),
  report: (days?: number) =>
    api.get('/compliance/report', { params: { days } }),
};

// Security API
export const securityAPI = {
  dashboard: () =>
    api.get('/security/dashboard'),
  threats: () =>
    api.get('/security/threats'),
  wafRules: () =>
    api.get('/security/waf/rules'),
  toggleWAF: (ruleId: string) =>
    api.post(`/security/waf/rules/${ruleId}/toggle`),
  events: (params?: { severity?: string; event_type?: string; limit?: number }) =>
    api.get('/security/events', { params }),
};

// Secrets API
export const secretsAPI = {
  audit: () =>
    api.get('/secrets/audit'),
  rotationCheck: () =>
    api.get('/secrets/rotation-check'),
  rotate: (name: string, newValue: string) =>
    api.post(`/secrets/${name}/rotate`, { new_value: newValue }),
};

// Disaster Recovery API
export const drAPI = {
  status: () =>
    api.get('/dr/status'),
  testResults: () =>
    api.get('/dr/test-results'),
  scenarios: () =>
    api.get('/dr/scenarios'),
};

// Chaos Engineering API
export const chaosEngAPI = {
  experiments: () =>
    api.get('/chaos-eng/experiments'),
  runExperiment: (name: string) =>
    api.post(`/chaos-eng/experiments/${name}/run`),
  emergencyStop: () =>
    api.post('/chaos-eng/emergency-stop'),
  resilienceScore: () =>
    api.get('/chaos-eng/resilience-score'),
  history: () =>
    api.get('/chaos-eng/history'),
  gamedayScenarios: () =>
    api.get('/chaos-eng/gameday/scenarios'),
  runGameday: (name: string) =>
    api.post(`/chaos-eng/gameday/${name}/run`),
  gamedayHistory: () =>
    api.get('/chaos-eng/gameday/history'),
};

// Database Optimization API
export const dbAPI = {
  analysis: () =>
    api.get('/db/analysis'),
};
