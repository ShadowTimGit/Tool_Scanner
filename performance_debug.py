import atexit
import os
import time
import tracemalloc
from collections import defaultdict
from contextlib import contextmanager


def _as_bool(value):
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


PERF_ENABLED = _as_bool(os.getenv("TOOL_SCANNER_PERF", "0"))
PERF_MEMORY = _as_bool(os.getenv("TOOL_SCANNER_PERF_MEMORY", "0"))
PERF_TOP_N = max(5, int(os.getenv("TOOL_SCANNER_PERF_TOP_N", "10")))


class PerfStat:
    __slots__ = ("count", "total", "max", "min", "peak_bytes", "contexts")

    def __init__(self):
        self.count = 0
        self.total = 0.0
        self.max = 0.0
        self.min = float("inf")
        self.peak_bytes = 0
        self.contexts = []

    def add(self, duration, peak_bytes=0, context=None):
        self.count += 1
        self.total += duration
        self.max = max(self.max, duration)
        self.min = min(self.min, duration)
        self.peak_bytes = max(self.peak_bytes, peak_bytes)

        if context:
            context_text = ", ".join(
                f"{key}={value}"
                for key, value in sorted(context.items())
                if value is not None
            )
            if context_text and len(self.contexts) < 8:
                self.contexts.append(context_text)

    def format(self, name):
        avg = self.total / self.count if self.count else 0.0
        peak_mb = self.peak_bytes / (1024 * 1024)
        context_text = ""
        if self.contexts:
            context_text = f" | contexts={self.contexts[0]}"
        return (
            f"{name:<42} count={self.count:>4} "
            f"total={self.total:>8.4f}s avg={avg:>8.4f}s "
            f"max={self.max:>8.4f}s min={self.min:>8.4f}s "
            f"peak={peak_mb:>7.2f}MB{context_text}"
        )


class PerfTracker:
    def __init__(self):
        self._stats = defaultdict(PerfStat)

    def record(self, name, duration, peak_bytes=0, **context):
        if not PERF_ENABLED:
            return
        self._stats[name].add(duration, peak_bytes=peak_bytes, context=context)

    @contextmanager
    def timer(self, name, **context):
        if not PERF_ENABLED:
            yield
            return

        start = time.perf_counter()
        peak_bytes = 0
        tracker_active = False

        if PERF_MEMORY:
            tracemalloc.start()
            tracker_active = True

        try:
            yield
        finally:
            duration = time.perf_counter() - start
            if tracker_active:
                current, peak = tracemalloc.get_traced_memory()
                peak_bytes = peak
                tracemalloc.stop()
            self.record(name, duration, peak_bytes=peak_bytes, **context)

    def summary(self):
        if not self._stats:
            return "[perf] no measurements captured."

        ranked = sorted(
            self._stats.items(),
            key=lambda item: (item[1].total, item[1].count),
            reverse=True,
        )

        lines = [
            "[perf] TOOL_SCANNER_PERF summary",
            "=" * 110,
        ]

        for name, stat in ranked[:PERF_TOP_N]:
            lines.append(stat.format(name))

        if len(ranked) > PERF_TOP_N:
            lines.append(f"... {len(ranked) - PERF_TOP_N} more measurements omitted")

        lines.append("=" * 110)
        return "\n".join(lines)


perf_tracker = PerfTracker()


def time_block(name, **context):
    return perf_tracker.timer(name, **context)


def print_perf_summary():
    if PERF_ENABLED:
        print(perf_tracker.summary())


if PERF_ENABLED:
    atexit.register(print_perf_summary)
