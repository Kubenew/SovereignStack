"""
Tests for SovereignStack Autonomous Operations
"""

import os
import tempfile
import time
import pytest
from services.autonomous_controller import AutonomousController, RemediationRule
from services.predictive_scheduler import ExponentialSmoothingModel, PredictiveScheduler

# ===========================================================================
# Autonomous Controller Tests
# ===========================================================================

@pytest.fixture
def temp_rules_file():
    fd, path = tempfile.mkstemp(suffix=".yaml")
    rules_content = """
remediation_rules:
  - alert_name: TestAlert
    action: RESTART_POD
    target: deployment/test-dep
    cooldown_seconds: 60
    """
    with os.fdopen(fd, 'w') as f:
        f.write(rules_content)
    yield path
    os.remove(path)


class TestAutonomousController:

    def test_load_rules(self, temp_rules_file):
        controller = AutonomousController(rules_path=temp_rules_file, dry_run=True)
        assert len(controller.rules) == 1
        assert "TestAlert" in controller.rules
        
        rule = controller.rules["TestAlert"]
        assert rule.action == "RESTART_POD"
        assert rule.target == "deployment/test-dep"
        assert rule.cooldown_seconds == 60

    def test_execute_action_cooldown(self, temp_rules_file):
        controller = AutonomousController(rules_path=temp_rules_file, dry_run=True)
        rule = controller.rules["TestAlert"]
        alert = {"labels": {"alertname": "TestAlert"}}
        
        # First execution should succeed
        assert controller.execute_action(rule, alert) is True
        
        # Immediate second execution should be blocked by cooldown
        assert controller.execute_action(rule, alert) is False

    def test_missing_rules_file_graceful(self):
        controller = AutonomousController(rules_path="/tmp/nonexistent-rules.yaml")
        assert len(controller.rules) == 0


# ===========================================================================
# Predictive Scheduler Tests
# ===========================================================================

class TestPredictiveScheduler:

    def test_exponential_smoothing_model(self):
        model = ExponentialSmoothingModel(alpha=0.5, beta=0.5)
        
        model.update(100.0)
        assert model.level == 100.0
        assert model.trend == 0.0
        
        model.update(110.0)
        # alpha=0.5, beta=0.5
        # level = 0.5 * 110 + 0.5 * 100 = 55 + 50 = 105
        # trend = 0.5 * (105 - 100) + 0.5 * 0 = 2.5
        assert model.level == 105.0
        assert model.trend == 2.5
        
        # predict 2 steps ahead: level + 2*trend = 105 + 5 = 110
        pred = model.predict(2)
        assert pred == 110.0

    def test_scheduler_threshold_trigger(self, monkeypatch):
        scheduler = PredictiveScheduler(prediction_window_seconds=120, polling_interval=60)
        
        # Mock fetch_metric to simulate increasing load
        def mock_fetch(query):
            if "gateway" in query:
                return 150.0 # Above threshold of 100
            return 50.0 # Below threshold
            
        monkeypatch.setattr(scheduler, "fetch_metric", mock_fetch)
        
        # Track triggers
        triggered = []
        def mock_trigger(name, pred):
            triggered.append(name)
            
        monkeypatch.setattr(scheduler, "_trigger_scale_up", mock_trigger)
        
        scheduler.update_models()
        scheduler.update_models() # Get a trend going
        scheduler.evaluate_predictions()
        
        assert "gateway_requests_rate" in triggered
        assert "vllm_gpu_utilization" not in triggered
