"""Tests for the Prediction Agent and forecasting components."""
import sys
import os
import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_prophet_forecaster_linear_fallback():
    """Test linear regression fallback when Prophet is not available."""
    from forecasting.prophet_forecaster import ProphetForecaster

    forecaster = ProphetForecaster(api_get=None)

    # Forecast with synthetic data (no API)
    result = forecaster.forecast_metric("test-service", "cpu", horizon_hours=24)

    assert "error" not in result or result.get("method") == "linear_regression"
    # Should still produce a result via linear or synthetic
    assert result.get("service") == "test-service"
    assert result.get("metric_name") == "cpu"


def test_prophet_forecaster_anomaly_detection():
    """Test anomaly detection on forecast results."""
    from forecasting.prophet_forecaster import ProphetForecaster
    from datetime import datetime, timedelta, timezone

    forecaster = ProphetForecaster(api_get=None)

    # Use future dates so hours_until calculation works
    now = datetime.now(timezone.utc)
    forecast_data = {
        "service_name": "api-server",
        "metric_name": "cpu",
        "method": "linear",
        "forecast": [
            {"ds": (now + timedelta(hours=6)).isoformat(), "yhat": 70, "yhat_lower": 65, "yhat_upper": 75},
            {"ds": (now + timedelta(hours=12)).isoformat(), "yhat": 80, "yhat_lower": 75, "yhat_upper": 85},
            {"ds": (now + timedelta(hours=18)).isoformat(), "yhat": 92, "yhat_lower": 87, "yhat_upper": 97},
            {"ds": (now + timedelta(hours=24)).isoformat(), "yhat": 95, "yhat_lower": 90, "yhat_upper": 100},
        ],
    }

    anomaly = forecaster.detect_anomalies_in_forecast(forecast_data)
    assert isinstance(anomaly, dict)
    # CPU threshold is 90, so forecast at 92 should trigger a breach
    assert anomaly["will_breach"] is True
    assert anomaly["hours_until_exhaustion"] is not None
    assert anomaly["hours_until_exhaustion"] > 0
    assert anomaly["severity"] in ("low", "medium", "high", "critical")


def test_prophet_forecaster_synthetic_history():
    """Test synthetic data generation for testing."""
    from forecasting.prophet_forecaster import ProphetForecaster

    forecaster = ProphetForecaster(api_get=None)

    history = forecaster._generate_synthetic_history(days=7)
    assert len(history) > 0
    # History returns [[timestamp_str, value], ...]
    assert isinstance(history[0], list)
    assert len(history[0]) == 2

    # Values should be reasonable
    values = [h[1] for h in history]
    assert min(values) >= -10  # small noise may go slightly below 0
    assert max(values) <= 110  # small noise may go slightly above base


def test_capacity_planner_current():
    """Test current capacity calculation."""
    from forecasting.capacity_planner import CapacityPlanner

    planner = CapacityPlanner(api_get=None)

    result = planner.calculate_current_capacity()
    assert "services" in result
    assert isinstance(result["services"], dict)

    # Each service should have utilization data
    for svc, data in result["services"].items():
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "status" in data
        assert data["status"] in ("healthy", "warning", "critical")


def test_capacity_planner_event_planning():
    """Test event-based capacity planning."""
    from forecasting.capacity_planner import CapacityPlanner
    from datetime import datetime, timedelta, timezone

    planner = CapacityPlanner(api_get=None)

    event_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    plan = planner.plan_for_event(
        event_date=event_date,
        expected_traffic_multiplier=3.0,
        event_name="Product Launch"
    )

    assert "event_name" in plan
    assert plan["event_name"] == "Product Launch"
    assert plan["traffic_multiplier"] == 3.0
    assert "actions" in plan
    assert "timeline" in plan


def test_capacity_planner_optimization():
    """Test resource optimization recommendations."""
    from forecasting.capacity_planner import CapacityPlanner

    planner = CapacityPlanner(api_get=None)

    optimizations = planner.optimize_resources()
    assert isinstance(optimizations, list)
    # May or may not have suggestions depending on random metrics


def test_trend_detector_degrading():
    """Test trend detection for degrading metrics."""
    from forecasting.trend_detector import TrendDetector

    detector = TrendDetector(api_get=None)

    # Without API, should handle gracefully
    trends = detector.detect_degrading_trends("test-service")
    assert isinstance(trends, list)


def test_trend_detector_correlation():
    """Test trend correlation between metrics."""
    from forecasting.trend_detector import TrendDetector

    detector = TrendDetector(api_get=None)

    correlations = detector.correlate_trends("test-service")
    assert isinstance(correlations, list)


def test_cost_forecaster_current():
    """Test current cost calculation."""
    from forecasting.cost_forecaster import CostForecaster

    forecaster = CostForecaster(api_get=None)

    costs = forecaster.calculate_current_costs()
    assert "current_monthly" in costs
    assert "breakdown" in costs
    assert costs["current_monthly"] > 0

    # Each service should have cost breakdown
    for svc, breakdown in costs["breakdown"].items():
        assert "compute" in breakdown
        assert "storage" in breakdown
        assert "network" in breakdown
        assert "total" in breakdown
        assert breakdown["total"] > 0


def test_cost_forecaster_monthly():
    """Test monthly cost forecast."""
    from forecasting.cost_forecaster import CostForecaster

    forecaster = CostForecaster(api_get=None)

    forecast = forecaster.forecast_monthly_cost()
    assert "current_monthly" in forecast
    assert "predicted_total" in forecast
    assert "growth_factor" in forecast
    assert "projected_breakdown" in forecast
    assert forecast["predicted_total"] >= forecast["current_monthly"]


def test_cost_forecaster_anomalies():
    """Test cost anomaly detection."""
    from forecasting.cost_forecaster import CostForecaster

    forecaster = CostForecaster(api_get=None)

    anomalies = forecaster.predict_cost_anomalies()
    assert isinstance(anomalies, list)


def test_cost_forecaster_optimization():
    """Test cost optimization recommendations."""
    from forecasting.cost_forecaster import CostForecaster

    forecaster = CostForecaster(api_get=None)

    optimizations = forecaster.optimize_for_cost()
    assert isinstance(optimizations, list)

    for opt in optimizations:
        assert "service" in opt
        assert "type" in opt
        assert "potential_savings" in opt
        assert opt["type"] in ("right_size", "reserved_instance")


def test_prediction_agent_init():
    """Test PredictionAgent initialization."""
    from prediction_agent import PredictionAgent

    agent = PredictionAgent()
    assert agent.name == "PredictionAgent"
    assert agent._tick_count == 0
    assert agent._forecaster is None  # Lazy init


def test_prediction_agent_incident_probability():
    """Test incident probability calculation."""
    from prediction_agent import PredictionAgent

    agent = PredictionAgent()
    # Without authentication, _init_components will create components with no API
    agent._init_components()

    result = agent.predict_incident_probability("test-service")
    assert "probability" in result
    assert "risk_level" in result
    assert "risk_factors" in result
    assert result["risk_level"] in ("low", "medium", "high", "critical")
    assert 0 <= result["probability"] <= 100


def test_prediction_agent_traffic_spike():
    """Test traffic spike prediction."""
    from prediction_agent import PredictionAgent

    agent = PredictionAgent()
    agent._init_components()

    spikes = agent.predict_traffic_spike()
    assert isinstance(spikes, list)


def test_prediction_agent_cost_forecast():
    """Test cost forecast through prediction agent."""
    from prediction_agent import PredictionAgent

    agent = PredictionAgent()
    agent._init_components()

    forecast = agent.forecast_costs()
    assert "current_monthly" in forecast
    assert "predicted_total" in forecast


def test_predictive_alert_manager():
    """Test PredictiveAlertManager priority scoring."""
    from prediction.predictive_alerts import PredictiveAlertManager

    manager = PredictiveAlertManager()

    alerts = [
        {"severity": "critical", "hours_until_issue": 2, "confidence": 90, "prediction_type": "resource_exhaustion"},
        {"severity": "low", "hours_until_issue": 72, "confidence": 50, "prediction_type": "degrading_trend"},
        {"severity": "high", "hours_until_issue": 12, "confidence": 80, "prediction_type": "capacity_breach"},
    ]

    prioritized = manager.prioritize_predictive_alerts(alerts)
    assert len(prioritized) == 3
    # Critical alert with 2h should be first
    assert prioritized[0]["severity"] == "critical"
    # Each should have a priority_score
    for alert in prioritized:
        assert "priority_score" in alert


def test_predictive_alert_prevention_actions():
    """Test suggested preventive actions."""
    from prediction.predictive_alerts import PredictiveAlertManager

    manager = PredictiveAlertManager()

    actions = manager.suggest_preventive_actions("resource_exhaustion")
    assert isinstance(actions, list)
    assert len(actions) > 0

    for action in actions:
        assert "action" in action
        assert "description" in action


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
