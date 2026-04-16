"""Trend analysis engine — regime changes, cyclical patterns, anomaly scoring."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from models.incident import Incident
from models.metric import Metric
from models.alert import Alert


class TrendAnalyzer:
    """Detects trends, regime changes, and cyclical patterns in system data."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    # ── Overall trend summary ──────────────────────────────────────────

    def trend_summary(self, days: int = 30) -> dict:
        since = datetime.utcnow() - timedelta(days=days)

        incidents = (
            self.db.query(Incident)
            .filter(Incident.user_id == self.user_id, Incident.detected_at >= since)
            .order_by(Incident.detected_at.asc())
            .all()
        )

        daily = self._bucket_daily(incidents, days)
        trend_dir, slope = self._linear_trend(daily)
        regime = self._detect_regime_change(daily)
        cyclical = self._detect_cyclical_pattern(incidents)

        return {
            "period_days": days,
            "total_incidents": len(incidents),
            "daily_counts": daily,
            "trend": trend_dir,
            "slope_per_day": round(slope, 3),
            "regime_change": regime,
            "cyclical_pattern": cyclical,
        }

    # ── Severity trends ────────────────────────────────────────────────

    def severity_trends(self, days: int = 30) -> dict:
        since = datetime.utcnow() - timedelta(days=days)
        incidents = (
            self.db.query(Incident)
            .filter(Incident.user_id == self.user_id, Incident.detected_at >= since)
            .all()
        )

        by_severity: dict[str, list] = defaultdict(list)
        for inc in incidents:
            day = inc.detected_at.strftime("%Y-%m-%d") if inc.detected_at else "unknown"
            by_severity[inc.severity].append(day)

        result = {}
        for sev in ["critical", "high", "medium", "low"]:
            counts = defaultdict(int)
            for d in by_severity.get(sev, []):
                counts[d] += 1
            daily_vals = list(counts.values()) if counts else [0]
            trend_dir, slope = self._linear_trend(daily_vals)
            result[sev] = {
                "total": len(by_severity.get(sev, [])),
                "daily_avg": round(sum(daily_vals) / max(len(daily_vals), 1), 2),
                "trend": trend_dir,
                "slope": round(slope, 3),
            }

        return {"period_days": days, "severity_trends": result}

    # ── Service health trends ──────────────────────────────────────────

    def service_trends(self, days: int = 30) -> dict:
        since = datetime.utcnow() - timedelta(days=days)
        incidents = (
            self.db.query(Incident)
            .filter(Incident.user_id == self.user_id, Incident.detected_at >= since)
            .all()
        )

        by_service: dict[str, list] = defaultdict(list)
        for inc in incidents:
            svc = inc.service_name or "unknown"
            by_service[svc].append(inc)

        result = {}
        for svc, incs in by_service.items():
            # Weekly comparison
            mid = datetime.utcnow() - timedelta(days=days // 2)
            first_half = [i for i in incs if i.detected_at and i.detected_at < mid]
            second_half = [i for i in incs if i.detected_at and i.detected_at >= mid]

            fh_count = len(first_half) or 1
            change_pct = round((len(second_half) - fh_count) / fh_count * 100, 1)

            result[svc] = {
                "total": len(incs),
                "first_half": len(first_half),
                "second_half": len(second_half),
                "change_pct": change_pct,
                "trend": "improving" if change_pct < -10 else "degrading" if change_pct > 10 else "stable",
                "critical_count": sum(1 for i in incs if i.severity == "critical"),
            }

        return {"period_days": days, "services": result}

    # ── Resolution efficiency trend ────────────────────────────────────

    def resolution_trends(self, days: int = 30) -> dict:
        since = datetime.utcnow() - timedelta(days=days)
        incidents = (
            self.db.query(Incident)
            .filter(
                Incident.user_id == self.user_id,
                Incident.detected_at >= since,
                Incident.resolved_at.isnot(None),
            )
            .order_by(Incident.detected_at.asc())
            .all()
        )

        if not incidents:
            return {"period_days": days, "resolution_times": [], "trend": "stable", "improving": False}

        weekly: dict[str, list[float]] = defaultdict(list)
        for inc in incidents:
            week = inc.detected_at.strftime("%Y-W%W")
            delta = (inc.resolved_at - inc.detected_at).total_seconds() / 60
            weekly[week].append(delta)

        weekly_avgs = []
        for wk in sorted(weekly.keys()):
            vals = weekly[wk]
            weekly_avgs.append({
                "week": wk,
                "avg_minutes": round(sum(vals) / len(vals), 1),
                "count": len(vals),
            })

        avgs_list = [w["avg_minutes"] for w in weekly_avgs]
        trend_dir, slope = self._linear_trend(avgs_list)
        # For resolution time, decreasing is improving
        improving = slope < 0

        return {
            "period_days": days,
            "weekly_resolution_times": weekly_avgs,
            "trend": "improving" if improving else "degrading" if slope > 0.5 else "stable",
            "improving": improving,
            "slope_minutes_per_week": round(slope, 2),
        }

    # ── Anomaly scoring ────────────────────────────────────────────────

    def anomaly_detection(self, days: int = 30) -> dict:
        since = datetime.utcnow() - timedelta(days=days)
        incidents = (
            self.db.query(Incident)
            .filter(Incident.user_id == self.user_id, Incident.detected_at >= since)
            .all()
        )

        daily = self._bucket_daily(incidents, days)
        if len(daily) < 3:
            return {"anomalies": [], "daily_counts": daily}

        mean = statistics.mean(daily)
        stdev = statistics.stdev(daily) if len(daily) > 1 else 1

        anomalies = []
        today = datetime.utcnow().date()
        for i, count in enumerate(daily):
            if stdev > 0:
                z = (count - mean) / stdev
            else:
                z = 0
            if abs(z) > 2:
                day_date = today - timedelta(days=days - 1 - i)
                anomalies.append({
                    "date": day_date.isoformat(),
                    "count": count,
                    "z_score": round(z, 2),
                    "type": "spike" if z > 0 else "dip",
                })

        return {
            "anomalies": anomalies,
            "daily_counts": daily,
            "mean": round(mean, 2),
            "stdev": round(stdev, 2),
            "threshold_z": 2.0,
        }

    # ── Helpers ─────────────────────────────────────────────────────────

    def _bucket_daily(self, incidents: list, days: int) -> list[int]:
        today = datetime.utcnow().date()
        buckets = [0] * days
        for inc in incidents:
            if inc.detected_at:
                day_offset = (today - inc.detected_at.date()).days
                idx = days - 1 - day_offset
                if 0 <= idx < days:
                    buckets[idx] += 1
        return buckets

    def _linear_trend(self, values: list) -> tuple[str, float]:
        n = len(values)
        if n < 2:
            return "stable", 0.0

        x_mean = (n - 1) / 2
        y_mean = sum(values) / n

        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den else 0

        if slope > 0.1:
            direction = "increasing"
        elif slope < -0.1:
            direction = "decreasing"
        else:
            direction = "stable"

        return direction, slope

    def _detect_regime_change(self, daily: list[int]) -> dict | None:
        if len(daily) < 10:
            return None

        mid = len(daily) // 2
        first = daily[:mid]
        second = daily[mid:]

        mean1 = statistics.mean(first)
        mean2 = statistics.mean(second)
        std1 = statistics.stdev(first) if len(first) > 1 else 1

        # Significant if difference > 2 standard deviations
        if std1 > 0 and abs(mean2 - mean1) > 2 * std1:
            return {
                "detected": True,
                "first_half_avg": round(mean1, 2),
                "second_half_avg": round(mean2, 2),
                "shift": "up" if mean2 > mean1 else "down",
                "significance": round(abs(mean2 - mean1) / std1, 2),
            }
        return None

    def _detect_cyclical_pattern(self, incidents: list) -> dict | None:
        if len(incidents) < 14:
            return None

        # Check day-of-week pattern
        dow_counts = defaultdict(int)
        for inc in incidents:
            if inc.detected_at:
                dow_counts[inc.detected_at.strftime("%A")] += 1

        if not dow_counts:
            return None

        vals = list(dow_counts.values())
        mean = sum(vals) / len(vals)
        if mean == 0:
            return None

        # High variance across days = cyclical
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        cv = (variance ** 0.5) / mean if mean > 0 else 0

        if cv > 0.3:
            peak_day = max(dow_counts, key=dow_counts.get)
            low_day = min(dow_counts, key=dow_counts.get)
            return {
                "detected": True,
                "type": "weekly",
                "peak_day": peak_day,
                "peak_count": dow_counts[peak_day],
                "low_day": low_day,
                "low_count": dow_counts[low_day],
                "day_distribution": dict(dow_counts),
            }
        return None
