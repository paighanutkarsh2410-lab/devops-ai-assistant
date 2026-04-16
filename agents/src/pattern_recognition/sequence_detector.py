"""
Sequence Detector: Detects event sequences (A → B → C = problem D)
with temporal relationships and sequence prediction.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class EventSequence:
    events: List[str]  # Ordered list of event types
    outcome: str  # What this sequence leads to
    occurrences: int = 0
    confidence: float = 0.0
    avg_duration_sec: float = 0.0


@dataclass
class SequenceMatch:
    sequence: EventSequence
    matched_events: List[dict]
    predicted_outcome: str
    confidence: float
    time_to_outcome_sec: float


class SequenceDetector:
    """Detects recurring event sequences and predicts outcomes."""

    def __init__(self, max_sequence_length: int = 5, time_window_sec: int = 3600):
        self._known_sequences: List[EventSequence] = []
        self._event_log: List[dict] = []  # {event_type, timestamp, service, details}
        self._max_len = max_sequence_length
        self._time_window = time_window_sec
        self._sequence_counts: Dict[tuple, Dict] = defaultdict(
            lambda: {"count": 0, "outcomes": defaultdict(int), "durations": []}
        )

    def add_known_sequence(self, events: List[str], outcome: str,
                           confidence: float = 80.0):
        """Register a known problematic sequence."""
        self._known_sequences.append(EventSequence(
            events=events, outcome=outcome,
            confidence=confidence,
        ))

    def record_event(self, event_type: str, timestamp: float,
                     service: str = "", details: dict = None):
        """Record an event for sequence analysis."""
        self._event_log.append({
            "event_type": event_type,
            "timestamp": timestamp,
            "service": service,
            "details": details or {},
        })

    def learn_sequences(self, events: List[dict] = None,
                        min_occurrences: int = 3) -> List[EventSequence]:
        """Discover recurring sequences from historical events."""
        events = events or self._event_log
        if len(events) < 5:
            return []

        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))

        # Slide windows and count n-gram sequences
        for window_size in range(2, self._max_len + 1):
            for i in range(len(sorted_events) - window_size):
                window = sorted_events[i:i + window_size]

                # Check time constraint
                duration = window[-1].get("timestamp", 0) - window[0].get("timestamp", 0)
                if duration > self._time_window:
                    continue

                seq_key = tuple(e.get("event_type", "") for e in window)

                # The event after this window is the "outcome"
                if i + window_size < len(sorted_events):
                    outcome_event = sorted_events[i + window_size]
                    outcome_type = outcome_event.get("event_type", "unknown")

                    self._sequence_counts[seq_key]["count"] += 1
                    self._sequence_counts[seq_key]["outcomes"][outcome_type] += 1
                    self._sequence_counts[seq_key]["durations"].append(duration)

        # Extract significant sequences
        discovered = []
        for seq_key, data in self._sequence_counts.items():
            if data["count"] < min_occurrences:
                continue

            # Most common outcome
            outcomes = data["outcomes"]
            if not outcomes:
                continue
            best_outcome = max(outcomes, key=outcomes.get)
            outcome_rate = outcomes[best_outcome] / data["count"]

            if outcome_rate > 0.5:  # >50% of the time leads to this outcome
                avg_dur = sum(data["durations"]) / len(data["durations"])
                seq = EventSequence(
                    events=list(seq_key),
                    outcome=best_outcome,
                    occurrences=data["count"],
                    confidence=round(outcome_rate * 100, 1),
                    avg_duration_sec=round(avg_dur, 1),
                )
                discovered.append(seq)
                self._known_sequences.append(seq)

        discovered.sort(key=lambda s: (-s.confidence, -s.occurrences))
        return discovered

    def detect_active_sequences(self, recent_events: List[dict] = None,
                                 lookback: int = 20) -> List[SequenceMatch]:
        """Check if any known sequences are currently unfolding."""
        events = recent_events or self._event_log[-lookback:]
        if not events or not self._known_sequences:
            return []

        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        event_types = [e.get("event_type", "") for e in sorted_events]
        matches = []

        for seq in self._known_sequences:
            pattern = seq.events
            plen = len(pattern)

            # Check if the pattern appears as a subsequence in recent events
            for start in range(len(event_types) - plen + 1):
                window = event_types[start:start + plen]
                if window == pattern:
                    matched = sorted_events[start:start + plen]
                    duration = matched[-1].get("timestamp", 0) - matched[0].get("timestamp", 0)

                    if duration <= self._time_window:
                        matches.append(SequenceMatch(
                            sequence=seq,
                            matched_events=matched,
                            predicted_outcome=seq.outcome,
                            confidence=seq.confidence,
                            time_to_outcome_sec=seq.avg_duration_sec - duration,
                        ))

                # Partial match — sequence in progress
                for partial_len in range(plen - 1, 0, -1):
                    partial = event_types[start:start + partial_len]
                    if partial == pattern[:partial_len]:
                        # Partial match found — predict the rest
                        remaining = pattern[partial_len:]
                        matched = sorted_events[start:start + partial_len]
                        matches.append(SequenceMatch(
                            sequence=seq,
                            matched_events=matched,
                            predicted_outcome=f"Partial ({partial_len}/{plen}): next expected → {remaining[0]}",
                            confidence=round(seq.confidence * (partial_len / plen), 1),
                            time_to_outcome_sec=seq.avg_duration_sec,
                        ))
                        break

        # Deduplicate and sort by confidence
        seen = set()
        unique = []
        for m in sorted(matches, key=lambda x: -x.confidence):
            key = (tuple(e.get("event_type") for e in m.matched_events), m.predicted_outcome)
            if key not in seen:
                seen.add(key)
                unique.append(m)

        return unique[:10]  # Top 10 matches

    def get_sequence_stats(self) -> dict:
        return {
            "known_sequences": len(self._known_sequences),
            "event_log_size": len(self._event_log),
            "top_sequences": [
                {
                    "events": s.events,
                    "outcome": s.outcome,
                    "occurrences": s.occurrences,
                    "confidence": s.confidence,
                }
                for s in sorted(self._known_sequences, key=lambda s: -s.confidence)[:10]
            ],
        }
