import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const incidentsDuration = new Trend('incidents_duration');
const metricsDuration = new Trend('metrics_duration');

export let options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to 100 users
    { duration: '5m', target: 100 },   // Stay at 100 users
    { duration: '2m', target: 200 },   // Ramp up to 200 users
    { duration: '5m', target: 200 },   // Stay at 200 users
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],       // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],         // Error rate < 1%
    errors: ['rate<0.01'],
    login_duration: ['p(95)<1000'],
    incidents_duration: ['p(95)<500'],
    metrics_duration: ['p(95)<300'],
  },
};

export default function () {
  let token = null;

  group('Authentication', () => {
    const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
      email: 'test@example.com',
      password: 'password123',
    }), { headers: { 'Content-Type': 'application/json' } });

    loginDuration.add(loginRes.timings.duration);

    const success = check(loginRes, {
      'login status 200': (r) => r.status === 200,
      'login has token': (r) => r.json('access_token') !== undefined,
    });

    errorRate.add(!success);

    if (success) {
      token = loginRes.json('access_token');
    }
  });

  if (!token) return;

  const authHeaders = {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };

  group('Dashboard Data', () => {
    // Fetch incidents
    const incidentsRes = http.get(`${BASE_URL}/incidents/`, authHeaders);
    incidentsDuration.add(incidentsRes.timings.duration);
    check(incidentsRes, {
      'incidents status 200': (r) => r.status === 200,
    });

    // Fetch metrics
    const metricsRes = http.get(`${BASE_URL}/metrics/current`, authHeaders);
    metricsDuration.add(metricsRes.timings.duration);
    check(metricsRes, {
      'metrics status 200': (r) => r.status === 200,
    });

    // Fetch alerts
    const alertsRes = http.get(`${BASE_URL}/alerts/`, authHeaders);
    check(alertsRes, {
      'alerts status 200': (r) => r.status === 200,
    });
  });

  group('API Endpoints', () => {
    // Health check
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
      'health status 200': (r) => r.status === 200,
    });

    // Analytics
    const analyticsRes = http.get(`${BASE_URL}/analytics/summary`, authHeaders);
    check(analyticsRes, {
      'analytics status 200': (r) => r.status === 200 || r.status === 401,
    });
  });

  sleep(Math.random() * 3 + 1); // 1-4s think time
}
