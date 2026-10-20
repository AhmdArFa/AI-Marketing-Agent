"""Run harness and tracing (Harness Engineering + Observability).

The harness is the controlled environment a brain run lives in: it owns the
run id, the span trace, the iteration count, and the recent trace store the
API exposes. The loop policy it enforces with the brain:

  - bounded iterations (a run may replan at most once),
  - one retry per failing compute tool, then degrade, never crash,
  - every phase and tool call lands in the trace with timing and status,
    so a bad run can be replayed from its trace alone.
"""

import time
import uuid
from collections import deque
from typing import Any, Dict, List

MAX_ITERATIONS = 2
TOOL_RETRIES = 1
TRACE_STORE: deque = deque(maxlen=50)


class HarnessRun:
    def __init__(self, session_id: str, goal: str) -> None:
        self.run_id = uuid.uuid4().hex[:12]
        self.session_id = session_id
        self.goal = goal
        self.iterations = 1
        self.spans: List[Dict[str, Any]] = []
        self.degraded = False
        self._started = time.perf_counter()

    def span(self, name: str, kind: str, status: str, duration_ms: float, detail: str = "") -> None:
        self.spans.append(
            {"name": name, "kind": kind, "status": status,
             "duration_ms": round(duration_ms, 2), "detail": detail[:200]}
        )

    def timed(self, name: str, kind: str, fn, detail: str = ""):
        started = time.perf_counter()
        try:
            out = fn()
            self.span(name, kind, "ok", (time.perf_counter() - started) * 1000, detail)
            return out
        except Exception as exc:
            self.span(name, kind, "error", (time.perf_counter() - started) * 1000, str(exc))
            raise

    def finish(self, status: str) -> Dict[str, Any]:
        trace = {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "iterations": self.iterations,
            "status": status,
            "degraded": self.degraded,
            "total_duration_ms": round((time.perf_counter() - self._started) * 1000, 2),
            "spans": self.spans,
        }
        TRACE_STORE.append(trace)
        return trace


def recent_traces(limit: int = 10) -> List[Dict[str, Any]]:
    return list(TRACE_STORE)[-limit:]
