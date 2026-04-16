"""Schemas for learning data, patterns, and action outcomes."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Learning Data ───────────────────────────────────────────────────────

class LearningDataCreate(BaseModel):
    pattern_type: str
    action_name: Optional[str] = None
    service_name: Optional[str] = None
    success: bool = False
    symptoms: Optional[Dict[str, Any]] = None

class LearningDataResponse(BaseModel):
    id: str
    pattern_type: str
    service_name: Optional[str]
    action_name: Optional[str]
    frequency: int
    success_rate: float
    total_attempts: int
    total_successes: int
    avg_resolution_time: float
    confidence: float
    symptoms: Optional[Dict[str, Any]]
    last_seen: Optional[datetime]

    class Config:
        from_attributes = True


# ── Action Outcome ──────────────────────────────────────────────────────

class ActionOutcomeCreate(BaseModel):
    incident_id: Optional[str] = None
    action_name: str
    incident_pattern: Optional[str] = None
    service_name: Optional[str] = None
    success: bool = False
    duration_seconds: float = 0.0
    impact_score: float = 0.0
    was_recommended: bool = False
    recommendation_rank: Optional[int] = None

class ActionOutcomeResponse(BaseModel):
    id: str
    incident_id: Optional[str]
    action_name: str
    incident_pattern: Optional[str]
    service_name: Optional[str]
    success: bool
    duration_seconds: float
    impact_score: float
    was_recommended: bool
    recommendation_rank: Optional[int]
    timestamp: Optional[datetime]

    class Config:
        from_attributes = True


# ── Pattern ─────────────────────────────────────────────────────────────

class PatternResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    pattern_type: str
    frequency: int
    confidence: float
    symptoms: Optional[Dict[str, Any]]
    common_root_causes: Optional[Dict[str, Any]]
    best_actions: Optional[Dict[str, Any]]
    affected_services: Optional[Dict[str, Any]]
    trending: str
    last_seen: Optional[datetime]

    class Config:
        from_attributes = True


# ── Recommendation ──────────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    incident_id: str

class RecommendationResponse(BaseModel):
    action_name: str
    confidence: float
    success_rate: float
    similar_count: int
    avg_similarity: float
    explanation: Optional[str] = None

class RecommendationListResponse(BaseModel):
    incident_id: str
    recommendations: List[RecommendationResponse]
    similar_incidents: List[Dict[str, Any]]


# ── Learning Insights ───────────────────────────────────────────────────

class LearningInsights(BaseModel):
    total_incidents_learned: int
    total_patterns_discovered: int
    detection_accuracy: float
    avg_resolution_time: float
    most_effective_action: Optional[str]
    knowledge_base_size: int
    improvement_rate: float
