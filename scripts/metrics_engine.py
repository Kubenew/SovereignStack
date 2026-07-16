#!/usr/bin/env python3
"""Rolling-window tokens-per-second performance tracker for inference nodes."""

from collections import deque


class NodePerformanceTracker:
    def __init__(self, window_size: int = 50):
        self.token_intervals = deque(maxlen=window_size)
        self.total_tokens_processed = 0

    def record_token_generation(self, tokens_count: int, duration_seconds: float):
        if duration_seconds <= 0:
            return
        tps = tokens_count / duration_seconds
        self.token_intervals.append(tps)
        self.total_tokens_processed += tokens_count

    def get_average_tps(self) -> float:
        if not self.token_intervals:
            return 0.0
        return sum(self.token_intervals) / len(self.token_intervals)


if __name__ == "__main__":
    tracker = NodePerformanceTracker()
    tracker.record_token_generation(tokens_count=120, duration_seconds=1.5)
    tracker.record_token_generation(tokens_count=210, duration_seconds=3.0)
    tracker.record_token_generation(tokens_count=45, duration_seconds=0.5)
    print(f"Total Processed: {tracker.total_tokens_processed} tokens")
    print(f"Rolling Avg Speed: {tracker.get_average_tps():.2f} Tokens/sec")
