from __future__ import annotations

import threading
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List

from config.settings import settings

# Internal storage for latencies and SLA breaches
_LATENCIES: Dict[str, List[float]] = defaultdict(list)
_SLA_BREACHES: Dict[str, int] = defaultdict(int)
_server: HTTPServer | None = None


def record_latency(phase: str, duration_ms: float, sla_ms: float | None = None) -> None:
    """Record latency for a given pipeline phase and check SLA."""
    _LATENCIES[phase].append(duration_ms)
    if sla_ms is not None and duration_ms > sla_ms:
        _SLA_BREACHES[phase] += 1


def get_average_latency(phase: str) -> float:
    """Return the average latency in milliseconds for a phase."""
    data = _LATENCIES.get(phase, [])
    return sum(data) / len(data) if data else 0.0


def get_sla_breaches(phase: str) -> int:
    """Return the number of SLA breaches for a phase."""
    return _SLA_BREACHES.get(phase, 0)


class _MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # type: ignore[override]
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        lines = []
        for phase, values in _LATENCIES.items():
            avg = get_average_latency(phase)
            lines.append(f"rag_{phase}_latency_ms {avg}")
            breaches = get_sla_breaches(phase)
            lines.append(f"rag_{phase}_sla_breaches_total {breaches}")
        self.wfile.write("\n".join(lines).encode())


def start_metrics_server(port: int = settings.metrics_port) -> None:
    """Start a simple HTTP server exposing metrics in Prometheus format."""
    global _server
    if _server is not None:
        return
    _server = HTTPServer(("0.0.0.0", port), _MetricsHandler)
    thread = threading.Thread(target=_server.serve_forever, daemon=True)
    thread.start()
