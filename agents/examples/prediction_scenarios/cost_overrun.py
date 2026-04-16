"""
Scenario: Cost Overrun Prediction
Demonstrates cost forecasting, anomaly detection, and optimization
recommendations for infrastructure cost management.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from forecasting.cost_forecaster import CostForecaster
from forecasting.capacity_planner import CapacityPlanner


def simulate_cost_overrun():
    """
    Simulate a multi-service infrastructure where costs are growing.
    The cost forecaster should detect the trend and recommend optimizations.
    """
    print("=" * 60)
    print("SCENARIO: Cost Overrun Prediction")
    print("=" * 60)

    cost_forecaster = CostForecaster(api_get=None)

    # 1. Current costs
    print("\n--- Current Monthly Costs ---")
    current = cost_forecaster.calculate_current_costs()
    print(f"  Total: ${current['current_monthly']:.2f}/month")
    print(f"  Calculated at: {current['calculated_at']}")

    for svc, breakdown in current["breakdown"].items():
        print(f"\n  {svc}:")
        print(f"    Compute:  ${breakdown['compute']:.2f} ({breakdown['instances']} instances)")
        print(f"    Storage:  ${breakdown['storage']:.2f}")
        print(f"    Network:  ${breakdown['network']:.2f}")
        print(f"    Total:    ${breakdown['total']:.2f}")

    # 2. Forecast
    print("\n--- Monthly Cost Forecast ---")
    forecast = cost_forecaster.forecast_monthly_cost()
    print(f"  Current:   ${forecast['current_monthly']:.2f}")
    print(f"  Predicted: ${forecast['predicted_total']:.2f}")
    print(f"  Change:    {forecast['change_percent']:+.1f}%")
    print(f"  Growth:    {forecast['growth_factor']:.3f}x")

    if forecast["change_percent"] > 30:
        print(f"\n  WARNING: Cost increase exceeds 30% threshold!")
        print(f"  This would trigger a cost_overrun predictive alert.")

    # 3. Cost anomalies
    print("\n--- Cost Anomalies ---")
    anomalies = cost_forecaster.predict_cost_anomalies()
    if anomalies:
        for a in anomalies:
            print(f"  {a['service']}: ${a['cost']:.0f}/month "
                  f"(avg: ${a['avg_cost']:.0f}, z-score: {a['z_score']:.1f})")
    else:
        print("  No cost anomalies detected")

    # 4. Optimization recommendations
    print("\n--- Cost Optimization Opportunities ---")
    optimizations = cost_forecaster.optimize_for_cost()
    if optimizations:
        total_savings = optimizations[0].get("total_potential_savings", 0)
        print(f"  Total potential savings: ${total_savings:.2f}/month\n")

        for opt in optimizations:
            print(f"  [{opt['risk']}] {opt['description']}")
            print(f"    Type: {opt['type']}")
            print(f"    Current cost: ${opt['current_cost']:.2f}")
            print(f"    Potential savings: ${opt['potential_savings']:.2f}")
            print(f"    Recommendation: {opt['recommendation']}")
            print()
    else:
        print("  No optimization opportunities identified")

    # 5. Capacity cost impact
    print("--- Capacity Planning Cost Impact ---")
    planner = CapacityPlanner(api_get=None)
    from datetime import datetime, timedelta, timezone

    event_date = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d")
    plan = planner.plan_for_event(event_date, 5.0, "Black Friday Sale")

    print(f"  Event: {plan['event_name']}")
    print(f"  Traffic multiplier: {plan['traffic_multiplier']}x")
    if "estimated_additional_cost" in plan:
        print(f"  Estimated additional cost: ${plan['estimated_additional_cost']:.2f}")

    print("\nScenario complete.")


if __name__ == "__main__":
    simulate_cost_overrun()
