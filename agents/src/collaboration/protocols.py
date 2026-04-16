"""
Collaboration Protocols: Defines structured interaction patterns between agents.
Supports request-response, broadcast, delegation, consensus, and peer review.
"""
import uuid
import time
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ProtocolType(str, Enum):
    REQUEST_RESPONSE = "request_response"
    BROADCAST = "broadcast"
    DELEGATION = "delegation"
    CONSENSUS = "consensus"
    PEER_REVIEW = "peer_review"


@dataclass
class Message:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sender: str = ""
    recipient: str = ""       # empty for broadcast
    protocol: str = ""
    msg_type: str = "request"  # request, response, broadcast, vote, review
    priority: str = "normal"   # low, normal, high, critical
    data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""   # links request/response pairs
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ttl_sec: float = 30.0
    status: str = "pending"


@dataclass
class ProtocolMetrics:
    total_exchanges: int = 0
    successful: int = 0
    failed: int = 0
    avg_latency_ms: float = 0.0
    timeouts: int = 0


class CollaborationProtocol:
    """
    Manages all collaboration protocols between agents.
    """

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._pending: Dict[str, Message] = {}
        self._responses: Dict[str, List[Message]] = {}
        self._metrics: Dict[str, ProtocolMetrics] = {p.value: ProtocolMetrics() for p in ProtocolType}
        self._lock = threading.Lock()
        self._conflict_history: List[Dict[str, Any]] = []

    # ── Agent Registration ────────────────────────────────────────────

    def register_handler(self, agent_name: str, handler: Callable[[Message], Message]):
        """Register an agent's message handler."""
        self._handlers[agent_name] = handler

    def unregister_handler(self, agent_name: str):
        self._handlers.pop(agent_name, None)

    # ── Request-Response ──────────────────────────────────────────────

    def request(self, sender: str, recipient: str, request_type: str,
                data: Dict[str, Any], priority: str = "normal",
                timeout: float = 30.0) -> Message:
        """
        Agent A requests help from Agent B and waits for response.
        """
        correlation_id = uuid.uuid4().hex[:12]
        msg = Message(
            sender=sender, recipient=recipient, protocol=ProtocolType.REQUEST_RESPONSE.value,
            msg_type="request", priority=priority, data={"request_type": request_type, **data},
            correlation_id=correlation_id, ttl_sec=timeout,
        )

        handler = self._handlers.get(recipient)
        if not handler:
            msg.status = "no_handler"
            self._track(ProtocolType.REQUEST_RESPONSE, success=False)
            return Message(
                sender=recipient, recipient=sender, msg_type="response",
                correlation_id=correlation_id, status="error",
                data={"error": f"Agent '{recipient}' not registered"},
            )

        start = time.time()
        try:
            response = handler(msg)
            latency = (time.time() - start) * 1000
            response.correlation_id = correlation_id
            response.sender = recipient
            response.recipient = sender
            response.msg_type = "response"
            self._track(ProtocolType.REQUEST_RESPONSE, success=True, latency_ms=latency)
            return response
        except Exception as e:
            self._track(ProtocolType.REQUEST_RESPONSE, success=False)
            return Message(
                sender=recipient, recipient=sender, msg_type="response",
                correlation_id=correlation_id, status="error",
                data={"error": str(e)},
            )

    # ── Broadcast ─────────────────────────────────────────────────────

    def broadcast(self, sender: str, question: str,
                  data: Dict[str, Any] = None,
                  exclude: List[str] = None) -> List[Message]:
        """
        Broadcast a message to all registered agents.
        Returns list of responses from interested agents.
        """
        exclude = exclude or [sender]
        data = data or {}
        correlation_id = uuid.uuid4().hex[:12]

        msg = Message(
            sender=sender, protocol=ProtocolType.BROADCAST.value,
            msg_type="broadcast", data={"question": question, **data},
            correlation_id=correlation_id,
        )

        responses = []
        for agent_name, handler in self._handlers.items():
            if agent_name in exclude:
                continue
            try:
                resp = handler(msg)
                if resp and resp.data.get("interested", True):
                    resp.sender = agent_name
                    resp.correlation_id = correlation_id
                    responses.append(resp)
            except Exception as e:
                logger.warning(f"[Protocol] Broadcast handler error from {agent_name}: {e}")

        self._track(ProtocolType.BROADCAST, success=len(responses) > 0)
        return responses

    # ── Delegation ────────────────────────────────────────────────────

    def delegate(self, coordinator: str, subtasks: List[Dict[str, Any]],
                 parallel: bool = True) -> Dict[str, Any]:
        """
        Coordinator delegates subtasks to specific agents.
        Each subtask: {"agent": "name", "task": "description", "data": {...}}
        """
        correlation_id = uuid.uuid4().hex[:12]
        results = {}

        def _run_task(task: Dict[str, Any]) -> tuple:
            agent = task["agent"]
            handler = self._handlers.get(agent)
            if not handler:
                return agent, {"error": f"Agent '{agent}' not available"}
            try:
                msg = Message(
                    sender=coordinator, recipient=agent,
                    protocol=ProtocolType.DELEGATION.value,
                    msg_type="request", data=task,
                    correlation_id=correlation_id,
                )
                resp = handler(msg)
                return agent, resp.data
            except Exception as e:
                return agent, {"error": str(e)}

        if parallel:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=len(subtasks)) as executor:
                futures = {executor.submit(_run_task, t): t for t in subtasks}
                for f in as_completed(futures, timeout=60):
                    agent, data = f.result()
                    results[agent] = data
        else:
            for task in subtasks:
                agent, data = _run_task(task)
                results[agent] = data

        self._track(ProtocolType.DELEGATION, success=True)
        return {
            "coordinator": coordinator,
            "correlation_id": correlation_id,
            "subtask_count": len(subtasks),
            "results": results,
        }

    # ── Consensus ─────────────────────────────────────────────────────

    def consensus(self, topic: str, agents: List[str],
                  data: Dict[str, Any] = None,
                  supermajority: float = 0.66) -> Dict[str, Any]:
        """
        Multiple agents vote on a topic. Weighted by confidence.
        Requires supermajority (default >66%) agreement.
        """
        data = data or {}
        correlation_id = uuid.uuid4().hex[:12]
        votes: List[Dict[str, Any]] = []

        msg = Message(
            protocol=ProtocolType.CONSENSUS.value, msg_type="vote_request",
            data={"topic": topic, **data}, correlation_id=correlation_id,
        )

        for agent_name in agents:
            handler = self._handlers.get(agent_name)
            if not handler:
                continue
            try:
                msg.recipient = agent_name
                resp = handler(msg)
                votes.append({
                    "agent": agent_name,
                    "vote": resp.data.get("vote", "abstain"),
                    "confidence": resp.data.get("confidence", 0.5),
                    "reasoning": resp.data.get("reasoning", ""),
                })
            except Exception:
                votes.append({"agent": agent_name, "vote": "abstain", "confidence": 0})

        # Weighted tally
        vote_groups: Dict[str, float] = {}
        total_weight = 0
        for v in votes:
            key = v["vote"]
            weight = v["confidence"]
            vote_groups[key] = vote_groups.get(key, 0) + weight
            total_weight += weight

        # Determine winner
        winner = max(vote_groups, key=vote_groups.get) if vote_groups else "no_consensus"
        winner_weight = vote_groups.get(winner, 0)
        agreement = winner_weight / max(total_weight, 0.001)
        consensus_reached = agreement >= supermajority

        result = {
            "topic": topic,
            "consensus_reached": consensus_reached,
            "winner": winner if consensus_reached else None,
            "agreement_pct": round(agreement * 100, 1),
            "required_pct": round(supermajority * 100, 1),
            "votes": votes,
            "vote_tally": {k: round(v, 2) for k, v in vote_groups.items()},
        }

        self._track(ProtocolType.CONSENSUS, success=consensus_reached)
        return result

    # ── Peer Review ───────────────────────────────────────────────────

    def peer_review(self, proposer: str, reviewer: str,
                    action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        One agent proposes an action, another reviews it.
        Returns approve/reject/modify decision.
        """
        correlation_id = uuid.uuid4().hex[:12]

        handler = self._handlers.get(reviewer)
        if not handler:
            return {
                "status": "no_reviewer",
                "action": action,
                "message": f"Reviewer '{reviewer}' not available",
            }

        msg = Message(
            sender=proposer, recipient=reviewer,
            protocol=ProtocolType.PEER_REVIEW.value,
            msg_type="review_request",
            data={"action": action, "context": context},
            correlation_id=correlation_id,
        )

        try:
            resp = handler(msg)
            decision = resp.data.get("decision", "reject")
            result = {
                "proposer": proposer,
                "reviewer": reviewer,
                "action": action,
                "decision": decision,  # approve, reject, modify
                "modifications": resp.data.get("modifications", []),
                "reasoning": resp.data.get("reasoning", ""),
                "safety_concerns": resp.data.get("safety_concerns", []),
            }
            self._track(ProtocolType.PEER_REVIEW, success=decision == "approve")
            return result
        except Exception as e:
            self._track(ProtocolType.PEER_REVIEW, success=False)
            return {"status": "error", "action": action, "error": str(e)}

    # ── Conflict Resolution ───────────────────────────────────────────

    def resolve_conflict(self, agents: Dict[str, Dict[str, Any]],
                         escalate_fn: Optional[Callable] = None) -> Dict[str, Any]:
        """
        When agents disagree, resolve using confidence-weighted voting.
        Falls back to escalation if no clear winner.
        """
        if not agents:
            return {"resolution": "no_input"}

        # Score each position
        positions: Dict[str, float] = {}
        for agent, position in agents.items():
            key = position.get("recommendation", "unknown")
            confidence = position.get("confidence", 0.5)
            positions[key] = positions.get(key, 0) + confidence

        winner = max(positions, key=positions.get)
        total = sum(positions.values())
        winner_pct = positions[winner] / max(total, 0.001)

        result = {
            "positions": {k: round(v, 2) for k, v in positions.items()},
            "winner": winner,
            "agreement_pct": round(winner_pct * 100, 1),
        }

        if winner_pct < 0.5:
            result["escalated"] = True
            result["reason"] = "No clear consensus — escalating to human"
            if escalate_fn:
                escalate_fn(result)
        else:
            result["escalated"] = False

        self._conflict_history.append(result)
        return result

    # ── Metrics ───────────────────────────────────────────────────────

    def _track(self, protocol: ProtocolType, success: bool, latency_ms: float = 0):
        with self._lock:
            m = self._metrics[protocol.value]
            m.total_exchanges += 1
            if success:
                m.successful += 1
            else:
                m.failed += 1
            if latency_ms:
                m.avg_latency_ms = (
                    (m.avg_latency_ms * (m.total_exchanges - 1) + latency_ms)
                    / m.total_exchanges
                )

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            p: {
                "total": m.total_exchanges,
                "successful": m.successful,
                "failed": m.failed,
                "avg_latency_ms": round(m.avg_latency_ms, 1),
            }
            for p, m in self._metrics.items()
        }
