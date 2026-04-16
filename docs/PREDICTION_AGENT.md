# Prediction Agent

The 5th agent in the pipeline. Forecasts infrastructure problems before they happen using time-series analysis, capacity planning, trend detection, and cost forecasting.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Prediction Agent                    │
│                (runs every 3600s)                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │   Prophet     │  │   Capacity   │                │
│  │  Forecaster   │  │   Planner    │                │
│  │  (or linear)  │  │              │                │
│  └──────┬───────┘  └──────┬───────┘                │
│         │                  │                        │
│  ┌──────┴───────┐  ┌──────┴───────┐                │
│  │    Trend     │  │     Cost     │                │
│  │   Detector   │  │  Forecaster  │                │
│  └──────┬───────┘  └──────┬───────┘                │
│         │                  │                        │
│  ┌──────┴──────────────────┴───────┐               │
│  │      Predictive Alert Manager    │               │
│  └──────────────┬──────────────────┘               │
│                 │                                   │
│         POST /alerts/predictive                     │
└─────────────────────────────────────────────────────┘
```

## Pipeline Position

```
Monitor → Diagnose → Remediate → Learn → Predict
  30s        60s        90s       120s     3600s
```

The Prediction Agent runs hourly, analyzing metric trends and generating forward-looking alerts. It complements the reactive pipeline (Monitor → Diagnose → Remediate) with proactive prevention.

## Components

### 1. Prophet Forecaster (`forecasting/prophet_forecaster.py`)

Time-series forecasting with Facebook Prophet (falls back to linear regression).

- **Metrics forecasted**: cpu, memory, disk, error_rate, response_time
- **Thresholds**: cpu(90%), memory(90%), disk(85%), error_rate(10%), response_time(1000ms)
- **Horizon**: 168 hours (7 days) default
- **Caching**: 1-hour TTL to avoid recomputation
- **Parallelism**: ThreadPoolExecutor(max_workers=4) for multi-metric forecasting

**Prophet settings:**
- Daily + weekly seasonality
- changepoint_prior_scale = 0.05
- 90% confidence interval

**Linear fallback:**
- numpy polyfit (degree 1) with 1.96×std confidence bands
- Always available, no external dependency

### 2. Capacity Planner (`forecasting/capacity_planner.py`)

Predicts when infrastructure capacity will be exceeded.

- **Current capacity**: Per-service utilization with health status
- **Breach prediction**: Forecasts when each metric exceeds threshold
- **Scaling recommendations**: Urgent (immediate) and planned (scheduled)
- **Resource optimization**: Identifies over-provisioned services (<20% utilization)
- **Event planning**: Pre-scale for known events (e.g., "Black Friday, 5x traffic")

### 3. Trend Detector (`forecasting/trend_detector.py`)

Identifies degrading trends across service metrics.

- **Linear regression**: Slope + R-squared analysis over 7-day windows
- **Moving averages**: Short (6h) vs long (24h) crossover detection
- **Severity mapping**: warning (2%/day) → critical (5%/day) per metric type
- **Seasonal anomalies**: Hourly baselines with z-score >2.5 detection
- **Trend correlation**: Finds metrics trending in the same direction

### 4. Cost Forecaster (`forecasting/cost_forecaster.py`)

Predicts and optimizes infrastructure costs.

- **Current costs**: Per-service breakdown (compute, storage, network)
- **Monthly forecast**: Projects next month using growth rate extrapolation
- **Anomaly detection**: Z-score analysis to find cost outliers
- **Optimization**: Right-sizing and reserved instance recommendations
- **Configurable pricing**: Loads from `config/pricing.yaml` or uses defaults

### 5. Predictive Alert Manager (`prediction/predictive_alerts.py`)

Creates, prioritizes, and tracks predictive alerts.

- **Priority scoring**: time_urgency × severity × confidence
- **Prevention actions**: Suggested actions per prediction type
- **Prevention tracking**: Mark alerts as prevented, track prevention rate
- **Prediction types**: resource_exhaustion, capacity_breach, degrading_trend, cost_overrun, anomaly_forecast

## Prediction Cycle

Each hourly tick performs:

| Step | Action | Frequency |
|------|--------|-----------|
| 1 | Forecast critical metrics (cpu, memory, disk, error_rate, response_time) | Every cycle |
| 2 | Detect degrading trends | Every cycle |
| 3 | Run capacity analysis | Every 6 cycles (~6 hours) |
| 4 | Run cost forecast | Every 24 cycles (~daily) |

## Alert Severity

Based on hours until predicted issue:

| Hours | Severity |
|-------|----------|
| < 6 | critical |
| < 24 | high |
| < 72 | medium |
| ≥ 72 | low |

## API Endpoints

### Predictive Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/alerts/predictive` | Create predictive alert |
| GET | `/alerts/predictive` | List predictive alerts |
| POST | `/alerts/predictive/{id}/prevent` | Mark alert as prevented |
| GET | `/alerts/predictive/stats` | Prevention statistics |

### Forecasts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predictions/metrics` | Metric forecasts |
| POST | `/predictions/metrics` | Store forecast |
| GET | `/predictions/capacity` | Capacity plans |
| POST | `/predictions/plan-event` | Plan for event |

### Costs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predictions/costs/current` | Current cost breakdown |
| GET | `/predictions/costs/forecast` | Monthly cost forecast |
| GET | `/predictions/costs/optimization` | Optimization recommendations |

### Trends
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predictions/trends` | Degrading trends |

## Database Models

### PredictiveAlert
Stores forward-looking alerts with prevention tracking.
- `prediction_type`: resource_exhaustion, capacity_breach, degrading_trend, cost_overrun
- `confidence`: 0-100% prediction confidence
- `hours_until_issue`: Time before predicted problem
- `prevented`: Whether action was taken to prevent
- `preventive_actions`: JSON list of suggested actions

### Forecast
Stores metric forecast results.
- `method`: prophet or linear
- `forecast_data`: JSON array of {ds, yhat, yhat_lower, yhat_upper}
- `breach_predicted`: Whether threshold breach is forecasted
- `hours_until_breach`: Time until predicted breach

### CapacityPlan
Stores capacity planning results and event plans.
- `plan_type`: forecast, event_scaling, optimization
- `recommendation`: Scaling recommendation text
- `additional_instances`: Number of extra instances needed
- `estimated_cost`: Cost of scaling

### CostForecast
Stores cost predictions and optimization results.
- `cost_breakdown`: JSON per-service cost details
- `optimizations`: JSON list of saving opportunities

## Graceful Degradation

| Component | Available | Fallback |
|-----------|-----------|----------|
| Prophet | Optional | Linear regression (numpy) |
| Backend API | Optional | Synthetic data for testing |
| Redis | Optional | Events logged but not published |
| Pricing config | Optional | Default pricing constants |

## Configuration

See `agents/config/predictions.yaml`:

```yaml
prediction:
  interval_seconds: 3600
  forecast_horizon_hours: 168
  history_days: 30
  min_confidence: 60

capacity:
  growth_buffer_percent: 20
  breach_alert_days: [7, 14, 30]

cost:
  alert_threshold_percent: 30
  pricing_config: config/pricing.yaml
```

## Example Scenarios

Run example scenarios from `agents/examples/prediction_scenarios/`:

```bash
cd agents
python examples/prediction_scenarios/disk_exhaustion.py
python examples/prediction_scenarios/traffic_spike.py
python examples/prediction_scenarios/cost_overrun.py
```

## Frontend

The Predictions page (`/predictions`) displays:

1. **Stats cards**: Total predictions, active alerts, prevented count, prevention rate
2. **Predictive Alerts tab**: Sorted by urgency, with prevention actions and "Mark Prevented" button
3. **Forecasts tab**: SVG charts with confidence bands and breach markers
4. **Capacity tab**: Per-service utilization bars with health status indicators
