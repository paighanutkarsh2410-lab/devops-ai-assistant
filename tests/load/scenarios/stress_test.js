import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');
const failedRequests = new Counter('failed_requests');

export let options = {
  stages: [
    { duration: '2m', target: 100 },    // Warm up
    { duration: '5m', target: 500 },    // Push to 500
    { duration: '5m', target: 1000 },   // Push to 1000
    { duration: '5m', target: 2000 },   // Push to breaking point
    { duration: '10m', target: 0 },     // Recovery
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],   // Relaxed for stress
    errors: ['rate<0.1'],                // 10% error acceptable under stress
  },
};

export default function () {
  // Health check (lightweight)
  const healthRes = http.get(`${BASE_URL}/health`);
  const healthOk = check(healthRes, {
    'health check ok': (r) => r.status === 200,
    'health response time < 1s': (r) => r.timings.duration < 1000,
  });
  errorRate.add(!healthOk);
  if (!healthOk) failedRequests.add(1);

  // Login
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'password123',
  }), { headers: { 'Content-Type': 'application/json' } });

  const loginOk = check(loginRes, {
    'login successful': (r) => r.status === 200 || r.status === 429,
  });
  errorRate.add(!loginOk);

  if (loginRes.status === 200) {
    const token = loginRes.json('access_token');
    const auth = { headers: { Authorization: `Bearer ${token}` } };

    // Concurrent API calls
    const responses = http.batch([
      ['GET', `${BASE_URL}/incidents/`, null, auth],
      ['GET', `${BASE_URL}/alerts/`, null, auth],
      ['GET', `${BASE_URL}/metrics/current`, null, auth],
    ]);

    for (const res of responses) {
      const ok = check(res, {
        'batch request ok': (r) => r.status === 200 || r.status === 429,
      });
      if (!ok) failedRequests.add(1);
    }
  }

  sleep(Math.random() * 2);
}
