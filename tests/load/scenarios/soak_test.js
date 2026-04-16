import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');
const memoryIndicator = new Trend('response_size_trend');
const totalRequests = new Counter('total_api_requests');

export let options = {
  stages: [
    { duration: '2m', target: 200 },     // Ramp up
    { duration: '3h', target: 200 },     // 3 hours sustained load
    { duration: '2m', target: 0 },       // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],     // Strict — no degradation over time
    http_req_failed: ['rate<0.01'],       // < 1% errors
    errors: ['rate<0.005'],              // < 0.5% application errors
  },
};

export default function () {
  // Login (cached token in real scenario)
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'password123',
  }), { headers: { 'Content-Type': 'application/json' } });

  if (loginRes.status !== 200) {
    errorRate.add(true);
    sleep(5);
    return;
  }

  const token = loginRes.json('access_token');
  const auth = { headers: { Authorization: `Bearer ${token}` } };
  totalRequests.add(1);

  // Simulate typical user session
  // 1. Check dashboard
  const dashRes = http.get(`${BASE_URL}/incidents/`, auth);
  check(dashRes, { 'dashboard ok': (r) => r.status === 200 });
  memoryIndicator.add(dashRes.body ? dashRes.body.length : 0);
  totalRequests.add(1);
  sleep(2);

  // 2. Check metrics
  const metricsRes = http.get(`${BASE_URL}/metrics/current`, auth);
  check(metricsRes, { 'metrics ok': (r) => r.status === 200 });
  totalRequests.add(1);
  sleep(1);

  // 3. Check alerts
  const alertsRes = http.get(`${BASE_URL}/alerts/`, auth);
  check(alertsRes, { 'alerts ok': (r) => r.status === 200 });
  totalRequests.add(1);
  sleep(1);

  // 4. Health check (memory leak indicator — response time should stay constant)
  const healthRes = http.get(`${BASE_URL}/health`);
  const healthOk = check(healthRes, {
    'health ok': (r) => r.status === 200,
    'health fast': (r) => r.timings.duration < 200,
  });
  errorRate.add(!healthOk);
  totalRequests.add(1);

  sleep(Math.random() * 5 + 3); // 3-8s between sessions
}
