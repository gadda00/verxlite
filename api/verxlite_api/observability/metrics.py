"""
Metrics Collector for Observability
"""

from collections import defaultdict
from typing import Any

from verxlite_api.utils.logger import get_logger

logger = get_logger("metrics")


class MetricsCollector:
    """
    Collects and tracks metrics for workflows.
    """

    def __init__(self):
        self.metrics = defaultdict(lambda: defaultdict(int))
        self.latencies = defaultdict(list)

    def track_workflow_run(
        self,
        workflow_type: str,
        status: str,
        duration_ms: int = 0,
        tokens_used: int = 0,
    ):
        """
        Track a workflow run.
        """
        key = f"workflow:{workflow_type}"
        self.metrics[key]["total_runs"] += 1

        if status == "completed":
            self.metrics[key]["successful_runs"] += 1
        else:
            self.metrics[key]["failed_runs"] += 1

        self.metrics[key]["total_tokens"] += tokens_used
        self.metrics[key]["total_duration_ms"] += duration_ms

        self.latencies[key].append(duration_ms)

        logger.debug(f"Tracked workflow run: {workflow_type}, status: {status}")

    def track_workflow_step(
        self,
        workflow_type: str,
        step_type: str,
        status: str,
        duration_ms: int = 0,
        tokens_used: int = 0,
    ):
        """
        Track a workflow step.
        """
        key = f"workflow:{workflow_type}:step:{step_type}"
        self.metrics[key]["total_steps"] += 1

        if status == "completed":
            self.metrics[key]["successful_steps"] += 1
        else:
            self.metrics[key]["failed_steps"] += 1

        self.metrics[key]["total_tokens"] += tokens_used
        self.metrics[key]["total_duration_ms"] += duration_ms

        self.latencies[key].append(duration_ms)

        logger.debug(f"Tracked workflow step: {workflow_type}/{step_type}, status: {status}")

    def get_metrics(self) -> dict[str, Any]:
        """
        Get all collected metrics.
        """
        result = {}

        for key, metrics in self.metrics.items():
            result[key] = dict(metrics)

            # Calculate averages
            if self.latencies[key]:
                result[key]["avg_duration_ms"] = sum(self.latencies[key]) / len(self.latencies[key])
                result[key]["p50_duration_ms"] = self._calculate_percentile(self.latencies[key], 50)
                result[key]["p90_duration_ms"] = self._calculate_percentile(self.latencies[key], 90)

            # Calculate success rate
            total = metrics.get("total_runs", metrics.get("total_steps", 1))
            successful = metrics.get("successful_runs", metrics.get("successful_steps", 0))
            result[key]["success_rate"] = successful / total if total > 0 else 0

        return result

    def _calculate_percentile(self, data: list, percentile: float) -> float:
        """
        Calculate percentile from a list of values.
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f

        if f == c:
            return sorted_data[f]

        return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)

    def reset(self):
        """
        Reset all metrics.
        """
        self.metrics.clear()
        self.latencies.clear()
