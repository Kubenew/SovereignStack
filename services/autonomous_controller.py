"""
SovereignStack Autonomous Controller

Self-healing and auto-scaling controller that polls Prometheus metrics
and alerts, applying declarative remediation actions.
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
import yaml

logger = logging.getLogger(__name__)


@dataclass
class RemediationRule:
    alert_name: str
    action: str
    target: str
    cooldown_seconds: int
    max_replicas: Optional[int] = None
    description: str = ""


class AutonomousController:
    """
    Polls Prometheus for firing alerts and executes remediation rules.
    Maintains a cooldown registry to prevent action flapping.
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        rules_path: str = "/app/config/autonomous-rules.yaml",
        dry_run: bool = False,
    ):
        self.prometheus_url = prometheus_url
        self.rules_path = rules_path
        self.dry_run = dry_run
        
        self.rules: Dict[str, RemediationRule] = {}
        self.last_action_time: Dict[str, float] = {}  # key: alert_name
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        self.load_rules()

    def load_rules(self) -> None:
        """Load remediation rules from YAML."""
        if not os.path.exists(self.rules_path):
            logger.warning("Rules file not found at %s", self.rules_path)
            return
            
        with open(self.rules_path, "r") as f:
            config = yaml.safe_load(f)
            
        for rule_data in config.get("remediation_rules", []):
            rule = RemediationRule(
                alert_name=rule_data["alert_name"],
                action=rule_data["action"],
                target=rule_data["target"],
                cooldown_seconds=rule_data.get("cooldown_seconds", 300),
                max_replicas=rule_data.get("max_replicas"),
                description=rule_data.get("description", ""),
            )
            self.rules[rule.alert_name] = rule
            
        logger.info("Loaded %d autonomous remediation rules", len(self.rules))

    def get_firing_alerts(self) -> List[dict]:
        """Fetch currently firing alerts from Prometheus."""
        try:
            url = f"{self.prometheus_url}/api/v1/alerts"
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                logger.error("Failed to fetch alerts: %s", resp.status_code)
                return []
                
            data = resp.json()
            if data.get("status") != "success":
                return []
                
            return [
                alert for alert in data.get("data", {}).get("alerts", [])
                if alert.get("state") == "firing"
            ]
        except Exception as exc:
            logger.error("Error connecting to Prometheus: %s", exc)
            return []

    def execute_action(self, rule: RemediationRule, alert: dict) -> bool:
        """Execute the defined remediation action."""
        now = time.time()
        last_time = self.last_action_time.get(rule.alert_name, 0)
        
        if now - last_time < rule.cooldown_seconds:
            logger.debug(
                "Skipping action %s for %s (cooldown: %ds remaining)",
                rule.action, rule.alert_name, rule.cooldown_seconds - (now - last_time)
            )
            return False
            
        logger.info(
            "AUTONOMOUS ACTION: Executing %s against %s (Trigger: %s)",
            rule.action, rule.target, rule.alert_name
        )
        
        if self.dry_run:
            logger.info("DRY RUN: Would execute %s", rule.action)
            self.last_action_time[rule.alert_name] = now
            return True
            
        # Implementation of actual K8s/Service API calls would go here
        # For the SovereignStack standard, we emit audit events and execute local shell/API commands
        success = self._run_remediation_logic(rule, alert)
        
        if success:
            self.last_action_time[rule.alert_name] = now
            
        return success

    def _run_remediation_logic(self, rule: RemediationRule, alert: dict) -> bool:
        """Mock implementation of remediation logic."""
        # In a real environment, this would use kubernetes python client
        if rule.action == "RESTART_POD":
            logger.info("-> Restarting pod %s", rule.target)
            return True
        elif rule.action == "EVICT_CACHE":
            logger.info("-> Evicting memory cache")
            return True
        elif rule.action == "SCALE_UP":
            logger.info("-> Scaling up %s (max %s)", rule.target, rule.max_replicas)
            return True
        elif rule.action == "ROTATE_LOGS":
            logger.info("-> Rotating logs on %s", rule.target)
            return True
        return False

    def loop(self) -> None:
        """Main reconciliation loop."""
        while self._running:
            alerts = self.get_firing_alerts()
            for alert in alerts:
                alert_name = alert.get("labels", {}).get("alertname")
                if not alert_name:
                    continue
                    
                rule = self.rules.get(alert_name)
                if rule:
                    self.execute_action(rule, alert)
                    
            time.sleep(15)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self.loop, daemon=True, name="autonomous-controller")
        self._thread.start()
        logger.info("Autonomous controller started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Autonomous controller stopped")
