"""Learning module: Pattern recognition, feedback loops, and recommendations."""
from .pattern_recognition import PatternRecognizer
from .correlation_matrix import CorrelationMatrix
from .feedback_loop import FeedbackLoop
from .recommendation_engine import RecommendationEngine
from .report_generator import LearningReportGenerator

__all__ = [
    "PatternRecognizer",
    "CorrelationMatrix",
    "FeedbackLoop",
    "RecommendationEngine",
    "LearningReportGenerator",
]
