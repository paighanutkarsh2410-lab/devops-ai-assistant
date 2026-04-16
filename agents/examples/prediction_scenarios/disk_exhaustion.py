"""
Scenario: Disk Exhaustion Prediction
Simulates a service with rapidly growing disk usage to demonstrate
how the Prediction Agent detects and alerts before disk fills up.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from forecasting.prophet_forecaster import ProphetForecaster
from forecasting.capacity_planner import CapacityPlanner


def simulate_disk_exhaustion():
    """
    Simulate a service where disk usage grows ~2% per day.
    At 60% now, the forecast should predict breach of 85% threshold
    in approximately 12-13 days.
    """
    print("=" * 60)
    print("SCENARIO: Disk Exhaustion Prediction")
    print("=" * 60)

    forecaster = ProphetForecaster(api_get=None)

    # Generate synthetic disk data with upward trend
    history = forecaster._generate_synthetic_history("disk", hours=168)

    # Inject a clear upward trend: start at ~60%, grow ~2%/day
    import numpy as np
    n = len(history)
    for i, point in enumerate(history):
        base = 60 + (i / n) * 14  # 60% → 74% over 7 days
        noise = np.random.normal(0, 1)
        point["y"] = min(95, max(10, base + noise))

    print(f"\nGenerated {n} hours of disk usage data")
    print(f"  Start: {history[0]['y']:.1f}%")
    print(f"  End:   {history[-1]['y']:.1f}%")

    # Forecast next 7 days
    forecast = forecaster.forecast_metric("log-server", "disk", horizon_hours=168)
    print(f"\nForecast method: {forecast.get('method', 'unknown')}")

    if forecast.get("forecast"):
        points = forecast["forecast"]
        print(f"  Forecasted points: {len(points)}")
        print(f"  Last predicted value: {points[-1].get('yhat', 0):.1f}%")

    # Check for anomalies
    anomaly = forecaster.detect_anomalies_in_forecast(forecast)
    if anomaly.get("will_breach"):
        hours = anomaly.get("hours_until_exhaustion", 0)
        print(f"\n  ALERT: Disk will breach 85% threshold in {hours:.0f} hours!")
        print(f"  Severity: {anomaly.get('severity', 'unknown')}")
    else:
        print("\n  No breach predicted within forecast horizon")

    # Capacity perspective
    print("\n--- Capacity Analysis ---")
    planner = CapacityPlanner(api_get=None)
    capacity = planner.calculate_current_capacity()

    for svc, data in capacity.get("services", {}).items():
        print(f"  {svc}: CPU={data.get('cpu_percent', 0):.0f}%, "
              f"Memory={data.get('memory_percent', 0):.0f}%, "
              f"Status={data.get('status', 'unknown')}")

    print("\nScenario complete.")


if __name__ == "__main__":
    simulate_disk_exhaustion()
