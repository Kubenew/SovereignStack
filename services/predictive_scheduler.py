"""
SovereignStack Predictive Scheduler

Uses time-series forecasting (Exponential Smoothing) on Prometheus metrics
to preemptively generate scale-up events before predicted demand spikes.
"""

import logging
import math
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class TimeSeriesPoint:
    timestamp: float
    value: float


class ExponentialSmoothingModel:
    """
    Simple Double Exponential Smoothing (Holt's Linear Trend) model.
    Lightweight, zero-dependency time series forecasting.
    """
    def __init__(self, alpha: float = 0.3, beta: float = 0.1):
        self.alpha = alpha
        self.beta = beta
        self.level: Optional[float] = None
        self.trend: Optional[float] = None
        
    def update(self, value: float) -> None:
        if self.level is None:
            self.level = value
            self.trend = 0.0
            return
            
        last_level = self.level
        self.level = self.alpha * value + (1 - self.alpha) * (last_level + self.trend)
        self.trend = self.beta * (self.level - last_level) + (1 - self.beta) * self.trend
        
    def predict(self, steps_ahead: int) -> float:
        if self.level is None:
            return 0.0
        return self.level + (steps_ahead * self.trend)


class PredictiveScheduler:
    """
    Polls historical metrics, updates forecasting models, and triggers
    preemptive scale-up if predicted load exceeds thresholds.
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        prediction_window_seconds: int = 300,
        polling_interval: int = 60,
    ):
        self.prometheus_url = prometheus_url
        self.prediction_window = prediction_window_seconds
        self.polling_interval = polling_interval
        
        # Models for specific metrics
        self.models: Dict[str, ExponentialSmoothingModel] = {
            "gateway_requests_rate": ExponentialSmoothingModel(),
            "vllm_gpu_utilization": ExponentialSmoothingModel(),
        }
        
        self.thresholds = {
            "gateway_requests_rate": 100.0,  # requests/sec
            "vllm_gpu_utilization": 0.85,    # 85% util
        }
        
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def fetch_metric(self, query: str) -> Optional[float]:
        """Fetch current value of a metric from Prometheus."""
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            resp = requests.get(url, params={"query": query}, timeout=5)
            if resp.status_code != 200:
                return None
                
            data = resp.json()
            results = data.get("data", {}).get("result", [])
            if not results:
                return None
                
            # Take sum across all instances
            total = sum(float(r["value"][1]) for r in results)
            return total
        except Exception as exc:
            logger.error("Failed to fetch metric %s: %s", query, exc)
            return None

    def update_models(self) -> None:
        """Fetch current metrics and update models."""
        queries = {
            "gateway_requests_rate": 'sum(rate(http_requests_total{job="gateway"}[1m]))',
            "vllm_gpu_utilization": 'avg(DCGM_FI_DEV_GPU_UTIL)',
        }
        
        for name, query in queries.items():
            val = self.fetch_metric(query)
            if val is not None:
                self.models[name].update(val)
                logger.debug("Updated model %s: val=%.2f, level=%.2f, trend=%.2f", 
                             name, val, self.models[name].level, self.models[name].trend)

    def evaluate_predictions(self) -> None:
        """Evaluate predictions and trigger preemptive scaling if needed."""
        # Assume polling_interval is 1 step. 
        steps = math.ceil(self.prediction_window / self.polling_interval)
        
        for name, model in self.models.items():
            pred = model.predict(steps)
            threshold = self.thresholds.get(name, float('inf'))
            
            if pred > threshold:
                logger.warning(
                    "PREDICTIVE SCALE-UP TRIGGERED: %s predicted to hit %.2f in %ds (threshold %.2f)",
                    name, pred, self.prediction_window, threshold
                )
                self._trigger_scale_up(name, pred)

    def _trigger_scale_up(self, metric_name: str, predicted_value: float) -> None:
        """Execute the actual scale-up logic (mocked)."""
        if metric_name == "gateway_requests_rate":
            logger.info("-> Emitting predictive scale-up event for gateway")
        elif metric_name == "vllm_gpu_utilization":
            logger.info("-> Emitting predictive scale-up event for vllm")

    def loop(self) -> None:
        """Main polling loop."""
        while self._running:
            self.update_models()
            self.evaluate_predictions()
            time.sleep(self.polling_interval)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self.loop, daemon=True, name="predictive-scheduler")
        self._thread.start()
        logger.info("Predictive scheduler started (window=%ds)", self.prediction_window)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Predictive scheduler stopped")
