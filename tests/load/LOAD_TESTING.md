# Load Testing Guide

## Overview

Load testing ensures the SentryAI can handle production-scale traffic. We use **k6** for HTTP load testing and a Python analysis layer for benchmark comparison and regression detection.

## Prerequisites

```bash
# Install k6
# macOS
brew install k6

# Linux (Debian/Ubuntu)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D68
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6

# Windows
choco install k6
# or download from https://k6.io/docs/getting-started/installation/
```

## Test Scenarios

| Scenario | File | VUs | Duration | Purpose |
|----------|------|-----|----------|---------|
| Normal Load | `scenarios/normal_load.js` | 100→200 | 16 min | Baseline performance |
| Stress Test | `scenarios/stress_test.js` | 100→2000 | 27 min | Find breaking point |
| Spike Test | `scenarios/spike_test.js` | 100→1000 | ~8 min | Sudden traffic surge |
| Soak Test | `scenarios/soak_test.js` | 200 | 3+ hours | Memory leaks, degradation |

## Running Tests

### Single Scenario
```bash
# Run normal load test
k6 run tests/load/scenarios/normal_load.js

# With custom base URL
k6 run -e BASE_URL=https://staging.example.com tests/load/scenarios/normal_load.js

# Export results as JSON
k6 run --summary-export=results.json tests/load/scenarios/normal_load.js
```

### All Scenarios (Python)
```bash
cd tests/load
python -c "from load_test_suite import LoadTestSuite; s = LoadTestSuite(); s.run_all_scenarios(); print(s.generate_report())"
```

### Analyze Results
```bash
python -c "
from analyze_results import ResultsAnalyzer
analyzer = ResultsAnalyzer()
data = analyzer.parse_k6_summary('results.json')
report = analyzer.generate_report(data)
import json; print(json.dumps(report, indent=2))
"
```

## Performance Benchmarks

| Metric | Target | Description |
|--------|--------|-------------|
| API p95 latency | < 200ms | 95th percentile response time |
| API p99 latency | < 500ms | 99th percentile response time |
| Error rate | < 1% | HTTP request failure rate |
| Throughput | > 500 req/s | Sustained request rate |
| DB query p95 | < 100ms | Database query performance |
| Dashboard load | < 2s | Frontend initial load time |
| Agent pipeline | < 5 min | Full agent processing cycle |
| Concurrent users | 1000+ | Simultaneous active users |

## Interpreting Results

### k6 Output
```
     ✓ login successful
     ✓ incidents retrieved

     http_req_duration..............: avg=145ms  min=12ms  p(95)=320ms  p(99)=485ms
     http_req_failed................: 0.23%  ✓ 45  ✗ 19555
     http_reqs......................: 19600  653.33/s
```

- **avg**: Average response time (aim for < 150ms)
- **p(95)**: 95% of requests faster than this (aim for < 200ms)
- **http_req_failed**: Error rate (aim for < 1%)
- **rate**: Requests per second (higher = better)

### Regression Detection
The analyzer compares current results against a saved baseline. Regressions are flagged when:
- **Info**: > 10% degradation
- **Warning**: > 20% degradation
- **Critical**: > 50% degradation

## CI/CD Integration

```yaml
# .github/workflows/load-test.yml
name: Nightly Load Test
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: grafana/k6-action@v0.3.1
        with:
          filename: tests/load/scenarios/normal_load.js
          flags: --summary-export=results.json
      - name: Analyze Results
        run: python tests/load/analyze_results.py results.json
```

## Optimization Guide

If benchmarks fail, consider:

1. **High latency**: Add response caching (Redis), optimize DB queries, enable connection pooling
2. **High error rate**: Increase rate limits, add retry logic, scale horizontally
3. **Low throughput**: Enable async processing, add worker instances, optimize middleware stack
4. **Memory leaks (soak test)**: Profile with py-spy, check for unclosed connections, review object lifecycle
