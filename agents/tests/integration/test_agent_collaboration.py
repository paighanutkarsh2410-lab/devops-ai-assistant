"""Integration tests for agent collaboration protocols and message bus."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from collaboration.protocols import CollaborationProtocol, Message, ProtocolType
from collaboration.message_bus import MessageBus, BusMessage


# ── Collaboration Protocol Tests ──────────────────────────────────────

def make_handler(name, response_data=None):
    """Create a test handler that returns response data."""
    def handler(msg: Message) -> Message:
        return Message(
            sender=name, msg_type="response", status="success",
            data=response_data or {"result": f"{name} processed", "confidence": 0.85},
        )
    return handler


class TestRequestResponse:
    def test_basic_request(self):
        proto = CollaborationProtocol()
        proto.register_handler("agent_b", make_handler("agent_b"))

        resp = proto.request("agent_a", "agent_b", "analyze", {"data": "test"})
        assert resp.status == "success"
        assert resp.data["result"] == "agent_b processed"

    def test_missing_handler(self):
        proto = CollaborationProtocol()
        resp = proto.request("agent_a", "missing_agent", "analyze", {})
        assert "error" in resp.data

    def test_metrics_tracked(self):
        proto = CollaborationProtocol()
        proto.register_handler("agent_b", make_handler("agent_b"))
        proto.request("agent_a", "agent_b", "analyze", {})

        stats = proto.stats
        assert stats["request_response"]["total"] == 1
        assert stats["request_response"]["successful"] == 1


class TestBroadcast:
    def test_broadcast_to_all(self):
        proto = CollaborationProtocol()
        proto.register_handler("agent_a", make_handler("agent_a"))
        proto.register_handler("agent_b", make_handler("agent_b"))
        proto.register_handler("agent_c", make_handler("agent_c"))

        responses = proto.broadcast("sender", "Any insights on this pattern?")
        assert len(responses) == 3

    def test_broadcast_excludes_sender(self):
        proto = CollaborationProtocol()
        proto.register_handler("sender", make_handler("sender"))
        proto.register_handler("other", make_handler("other"))

        responses = proto.broadcast("sender", "Question?")
        assert len(responses) == 1
        assert responses[0].sender == "other"


class TestConsensus:
    def test_consensus_reached(self):
        proto = CollaborationProtocol()

        def vote_handler(msg):
            return Message(data={"vote": "restart", "confidence": 0.9, "reasoning": "Best option"})

        proto.register_handler("a", vote_handler)
        proto.register_handler("b", vote_handler)
        proto.register_handler("c", vote_handler)

        result = proto.consensus("What action?", ["a", "b", "c"])
        assert result["consensus_reached"]
        assert result["winner"] == "restart"
        assert result["agreement_pct"] == 100.0

    def test_consensus_not_reached(self):
        proto = CollaborationProtocol()

        proto.register_handler("a", lambda m: Message(data={"vote": "restart", "confidence": 0.5}))
        proto.register_handler("b", lambda m: Message(data={"vote": "scale", "confidence": 0.5}))
        proto.register_handler("c", lambda m: Message(data={"vote": "rollback", "confidence": 0.5}))

        result = proto.consensus("What action?", ["a", "b", "c"], supermajority=0.66)
        assert not result["consensus_reached"]


class TestPeerReview:
    def test_approve(self):
        proto = CollaborationProtocol()
        proto.register_handler("reviewer", lambda m: Message(
            data={"decision": "approve", "reasoning": "Safe to proceed"}
        ))

        result = proto.peer_review("proposer", "reviewer", "restart_service", {})
        assert result["decision"] == "approve"

    def test_reject(self):
        proto = CollaborationProtocol()
        proto.register_handler("reviewer", lambda m: Message(
            data={"decision": "reject", "reasoning": "Too risky",
                  "safety_concerns": ["Production hours"]}
        ))

        result = proto.peer_review("proposer", "reviewer", "restart_service", {})
        assert result["decision"] == "reject"
        assert len(result["safety_concerns"]) == 1


class TestDelegation:
    def test_delegate_subtasks(self):
        proto = CollaborationProtocol()
        proto.register_handler("agent_a", make_handler("agent_a", {"analysis": "done"}))
        proto.register_handler("agent_b", make_handler("agent_b", {"scan": "complete"}))

        result = proto.delegate("coordinator", [
            {"agent": "agent_a", "task": "analyze_logs"},
            {"agent": "agent_b", "task": "scan_metrics"},
        ])
        assert result["subtask_count"] == 2
        assert "agent_a" in result["results"]
        assert "agent_b" in result["results"]


# ── Message Bus Tests ─────────────────────────────────────────────────

class TestMessageBus:
    def test_pubsub(self):
        bus = MessageBus()
        received = []
        bus.subscribe("alerts", lambda m: received.append(m))
        bus.publish("alerts", "monitor", {"severity": "critical"})
        assert len(received) == 1
        assert received[0].payload["severity"] == "critical"

    def test_point_to_point(self):
        bus = MessageBus()
        bus.send("agent_b", "agent_a", {"task": "analyze"})
        messages = bus.receive("agent_b")
        assert len(messages) == 1
        assert messages[0].payload["task"] == "analyze"

    def test_dead_letter_queue(self):
        bus = MessageBus()
        bus.subscribe("failing", lambda m: (_ for _ in ()).throw(Exception("fail")))
        bus.publish("failing", "sender", {"data": "test"})
        dead = bus.get_dead_letters()
        assert len(dead) == 1

    def test_stats(self):
        bus = MessageBus()
        received = []
        bus.subscribe("test", lambda m: received.append(m))
        bus.publish("test", "sender", {"a": 1})
        bus.publish("test", "sender", {"b": 2})
        assert bus.stats["published"] == 2
        assert bus.stats["delivered"] == 2
