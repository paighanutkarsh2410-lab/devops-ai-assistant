"""Tests for the Learning Agent and related components."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_pattern_recognition():
    """Test pattern extraction from incident data."""
    from learning.pattern_recognition import PatternRecognizer

    recognizer = PatternRecognizer()

    # Memory leak pattern
    incident = {
        "title": "High memory usage on api-server",
        "description": "Memory keeps growing, possible memory leak",
        "root_cause": "Memory leak in request handler",
        "service_name": "api-server",
        "severity": "high",
        "detected_at": "2024-01-15T14:30:00Z",
    }
    pattern = recognizer.extract_incident_pattern(incident)
    assert pattern["pattern_type"] == "memory_leak"
    assert pattern["confidence"] > 0

    # CPU spike pattern
    cpu_incident = {
        "title": "CPU spike on worker-service",
        "description": "CPU at 95%",
        "root_cause": "High CPU from infinite loop",
        "service_name": "worker-service",
        "severity": "critical",
    }
    pattern = recognizer.extract_incident_pattern(cpu_incident)
    assert pattern["pattern_type"] == "cpu_spike"


def test_pattern_frequency():
    """Test pattern frequency calculation."""
    from learning.pattern_recognition import PatternRecognizer

    recognizer = PatternRecognizer()
    incidents = [
        {"title": "Memory leak on svc-a", "root_cause": "memory issue", "detected_at": "2024-01-15T10:00:00Z"},
        {"title": "Memory OOM on svc-b", "root_cause": "out of memory", "detected_at": "2024-01-16T10:00:00Z"},
        {"title": "CPU spike on svc-c", "root_cause": "high cpu", "detected_at": "2024-01-17T10:00:00Z"},
    ]

    freq = recognizer.calculate_pattern_frequency(incidents)
    assert "memory_leak" in freq
    assert freq["memory_leak"]["count"] == 2
    assert "cpu_spike" in freq
    assert freq["cpu_spike"]["count"] == 1


def test_correlation_matrix():
    """Test correlation matrix updates and predictions."""
    from learning.correlation_matrix import CorrelationMatrix

    matrix = CorrelationMatrix()

    pattern = {
        "pattern_type": "memory_leak",
        "symptoms": {"metric_spikes": ["memory"], "service": "api-server"},
        "time_info": {"hour_bucket": "afternoon", "day_of_week": "Monday"},
    }
    incident = {"root_cause": "Memory leak in handler", "solution": "restart_service", "service_name": "api-server"}

    matrix.update_from_incident(incident, pattern)
    matrix.update_from_incident(incident, pattern)  # Second time

    # Should predict root cause
    predictions = matrix.predict_root_cause({"metric_spikes": ["memory"]})
    assert len(predictions) > 0
    assert "Memory leak" in predictions[0]["root_cause"]

    # Should suggest solution
    solutions = matrix.suggest_solution("Memory leak in handler")
    assert len(solutions) > 0
    assert solutions[0]["solution"] == "restart_service"

    # Service profile
    profile = matrix.get_service_profile("api-server")
    assert profile["total_incidents"] == 2


def test_feedback_loop():
    """Test feedback loop outcome recording and preference updates."""
    from learning.feedback_loop import FeedbackLoop

    # Use temp path to avoid persisting test data
    import tempfile
    temp_dir = tempfile.mkdtemp()
    loop = FeedbackLoop()
    loop._data_path = os.path.join(temp_dir, "test_feedback.json")

    # Record outcomes
    loop.record_outcome("inc-1", "restart_service", True, "memory_leak")
    loop.record_outcome("inc-2", "restart_service", True, "memory_leak")
    loop.record_outcome("inc-3", "restart_service", False, "memory_leak")

    # Check ranking
    ranking = loop.get_action_ranking("memory_leak")
    assert len(ranking) > 0
    assert ranking[0]["action_name"] == "restart_service"
    assert ranking[0]["total"] == 3
    assert ranking[0]["success_rate"] == pytest.approx(66.7, abs=0.1)

    # Detection stats
    loop.record_detection(True, True)
    loop.record_detection(False, True)
    accuracy = loop.get_detection_accuracy()
    assert accuracy["precision"] == 50.0
    assert accuracy["recall"] == 100.0


def test_recommendation_engine():
    """Test recommendation scoring and ranking."""
    from learning.recommendation_engine import RecommendationEngine

    engine = RecommendationEngine()

    incident = {"title": "API timeout", "service_name": "api-server"}
    similar = [
        {"action_taken": "restart_service", "score": 0.9, "success": True, "resolution_time": 30},
        {"action_taken": "restart_service", "score": 0.85, "success": True, "resolution_time": 45},
        {"action_taken": "scale_service", "score": 0.8, "success": False, "resolution_time": 120},
        {"action_taken": "restart_service", "score": 0.7, "success": True, "resolution_time": 60},
    ]

    recs = engine.recommend_actions(incident, similar, top_k=3)
    assert len(recs) > 0
    # restart_service should be #1 (3 successes, high similarity)
    assert recs[0]["action_name"] == "restart_service"
    assert recs[0]["success_rate"] == 100.0
    assert recs[0]["similar_count"] == 3

    # Test explanation
    explanation = engine.explain_recommendation("restart_service", similar)
    assert "3 out of 3" in explanation or "worked in" in explanation


def test_embedding_fallback():
    """Test that embedding generation works even without sentence-transformers."""
    from knowledge_base.embeddings import _fallback_embedding, VECTOR_SIZE

    embedding = _fallback_embedding("test incident memory leak")
    assert len(embedding) == VECTOR_SIZE
    # Should be normalized
    import numpy as np
    norm = np.linalg.norm(embedding)
    assert abs(norm - 1.0) < 0.01


def test_report_generator():
    """Test report generator insight generation."""
    from learning.report_generator import LearningReportGenerator

    generator = LearningReportGenerator()

    # Without API, should return empty insights gracefully
    insights = generator.generate_learning_insights()
    assert isinstance(insights, list)

    gaps = generator.identify_knowledge_gaps()
    assert isinstance(gaps, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
