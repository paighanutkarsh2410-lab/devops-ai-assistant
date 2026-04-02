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

// Alerts API
export const alertsAPI = {
  getAll: (params?: { acknowledged?: boolean; resolved?: boolean; severity?: string; limit?: number }) =>
    api.get('/alerts/', { params }),

  update: (id: string, data: { acknowledged?: boolean; resolved?: boolean }) =>
    api.patch(`/alerts/${id}`, data),
};
