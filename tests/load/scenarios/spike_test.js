import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');
const recoveryTime = new Trend('recovery_time');

export let options = {
  stages: [
    { duration: '10s', target: 100 },    // Baseline
    { duration: '1m', target: 1000 },    // Sudden spike
    { duration: '3m', target: 1000 },    // Sustained spike
    { duration: '10s', target: 100 },    // Drop back
    { duration: '3m', target: 100 },     // Recovery period
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'],    // Relaxed during spike
    errors: ['rate<0.05'],                // 5% acceptable during spike
  },
};

export default function () {
  const start = Date.now();

  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health available': (r) => r.status === 200,
  });

  // Login
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'password123',
  }), { headers: { 'Content-Type': 'application/json' } });

  const loginOk = check(loginRes, {
    'login ok or rate limited': (r) => r.status === 200 || r.status === 429,
  });
  errorRate.add(!loginOk);

  if (loginRes.status === 200) {
    const token = loginRes.json('access_token');
    const auth = { headers: { Authorization: `Bearer ${token}` } };

    // Dashboard data
    const incidentsRes = http.get(`${BASE_URL}/incidents/`, auth);
    check(incidentsRes, {
      'incidents retrieved': (r) => r.status === 200,
    });

    // Track recovery — how fast requests return to normal latency
    recoveryTime.add(Date.now() - start);
  }

  sleep(Math.random() + 0.5);
}
