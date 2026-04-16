"""
Scenario: Traffic Spike Prediction
Simulates a service experiencing gradually increasing response times,
predicting a traffic spike before it causes user-facing issues.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from forecasting.prophet_forecaster import ProphetForecaster
from forecasting.trend_detector import TrendDetector
from prediction.predictive_alerts import PredictiveAlertManager


def simulate_traffic_spike():
    """
    Simulate increasing response times on an API service.
    The Prediction Agent should detect the degrading trend and
    alert before response times breach the 1000ms threshold.
    """
    print("=" * 60)
    print("SCENARIO: Traffic Spike Prediction")
    print("=" * 60)

    forecaster = ProphetForecaster(api_get=None)
    detector = TrendDetector(api_get=None)
    alert_mgr = PredictiveAlertManager()

    # Forecast response time
    forecast = forecaster.forecast_metric("api-server", "response_time", horizon_hours=24)
    print(f"\nResponse time forecast for api-server:")
    print(f"  Method: {forecast.get('method', 'unknown')}")

    if forecast.get("trend"):
        trend = forecast["trend"]
        print(f"  Direction: {trend.get('direction', 'unknown')}")
        print(f"  Change over horizon: {trend.get('change_over_horizon', 0):.1f}ms")

    # Check for threshold breach
    anomaly = forecaster.detect_anomalies_in_forecast(forecast)
    if anomaly.get("will_breach"):
        hours = anomaly.get("hours_until_exhaustion", 0)
        print(f"\n  ALERT: Response time will breach 1000ms in {hours:.0f} hours!")
        print(f"  Severity: {anomaly.get('severity')}")

        # Generate preventive actions
        actions = alert_mgr.suggest_preventive_actions("degrading_trend", "api-server")
        print(f"\n  Suggested preventive actions:")
        for action in actions:
            print(f"    - [{action.get('effort', '?')}] {action.get('description', '')}")
    else:
        print("\n  No threshold breach predicted")

    # Priority scoring
    print("\n--- Alert Priority Scoring ---")
    test_alerts = [
        {
            "title": "Response time degrading on api-server",
            "severity": "high",
            "hours_until_issue": 8,
            "confidence": 80,
            "prediction_type": "degrading_trend",
        },
        {
            "title": "CPU spike predicted on worker-service",
            "severity": "critical",
            "hours_until_issue": 3,
            "confidence": 90,
            "prediction_type": "resource_exhaustion",
        },
    ]

    prioritized = alert_mgr.prioritize_predictive_alerts(test_alerts)
    for alert in prioritized:
        print(f"  Score {alert['priority_score']:.1f}: {alert['title']} "
              f"(severity={alert['severity']}, {alert.get('hours_until_issue', '?')}h)")

    print("\nScenario complete.")


if __name__ == "__main__":
    simulate_traffic_spike()
