"""Chaos engineering API endpoints."""
import sys
import os
from fastapi import APIRouter, Depends
from utils.auth import get_current_user

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tests", "chaos"))

router = APIRouter(prefix="/chaos-eng", tags=["chaos-engineering"])

_suite = None
_gameday = None


def _get_suite():
    global _suite
    if _suite is None:
        from chaos_suite import ChaosSuite, SafetyControls
        _suite = ChaosSuite(safety=SafetyControls(require_approval=False))
        # Seed some demo history
        for name in ["kill_random_service", "network_latency", "cpu_spike", "database_connection_drop"]:
            _suite.run_experiment(name, approved=True)
    return _suite


def _get_gameday():
    global _gameday
    if _gameday is None:
        from gameday import GameDay
        _gameday = GameDay()
        _gameday.run_scenario("Cascading Service Failure")
        _gameday.run_scenario("Agent Swarm Failure")
    return _gameday


@router.get("/experiments")
def list_experiments(current_user=Depends(get_current_user)):
    """List all chaos experiments."""
    return {"experiments": _get_suite().list_experiments()}


@router.post("/experiments/{name}/run")
def run_experiment(name: str, current_user=Depends(get_current_user)):
    """Run a chaos experiment."""
    return _get_suite().run_experiment(name, approved=True)


@router.post("/emergency-stop")
def emergency_stop(current_user=Depends(get_current_user)):
    """Emergency stop all chaos experiments."""
    _get_suite().emergency_stop()
    return {"status": "emergency_stop_activated"}


@router.get("/resilience-score")
def resilience_score(current_user=Depends(get_current_user)):
    """Get system resilience score."""
    return _get_suite().get_resilience_score()


@router.get("/history")
def experiment_history(current_user=Depends(get_current_user)):
    """Get experiment execution history."""
    return {"history": _get_suite().get_history()}


@router.get("/gameday/scenarios")
def gameday_scenarios(current_user=Depends(get_current_user)):
    """List game day scenarios."""
    return {"scenarios": _get_gameday().get_all_scenarios()}


@router.post("/gameday/{scenario_name}/run")
def run_gameday(scenario_name: str, current_user=Depends(get_current_user)):
    """Run a game day scenario."""
    try:
        result = _get_gameday().run_scenario(scenario_name)
        return {
            "scenario": result.scenario_name,
            "score": result.team_score,
            "detected": result.incidents_detected,
            "resolved": result.incidents_resolved,
            "criteria_met": [c for c in result.success_criteria_met],
            "lessons": result.lessons_learned,
        }
    except ValueError as e:
        return {"error": str(e)}


@router.get("/gameday/history")
def gameday_history(current_user=Depends(get_current_user)):
    """Get game day history."""
    return {"history": _get_gameday().get_history()}
