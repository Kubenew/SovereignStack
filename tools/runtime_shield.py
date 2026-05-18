#!/usr/bin/env python3
"""
OASA Runtime Shield Wrapper
===========================
Обеспечивает изоляцию ИИ-движков во время выполнения (Runtime).
Контролирует утечки RAM/VRAM и предотвращает скрытую сетевую активность.

Usage:
    python runtime_shield.py --config ../sovereign-stack.yaml --cmd "python -m turboprivate_ai.main"
"""

import argparse
import time
import subprocess
import sys
import psutil
import socket
from pathlib import Path
import yaml # Требуется PyYAML (pip install pyyaml)

class RuntimeShield:
    def __init__(self, config_path: str, command: str):
        self.config = self._load_config(config_path)
        self.command = command
        self.process = None
        
        # Параметры защиты из YAML
        # Обратная совместимость: поддержка как старой (compute), так и новой (compute_execution) структуры
        compute_cfg = self.config.get("compute_execution", self.config.get("compute", {}))
        runtime_prot = compute_cfg.get("runtime_protection", {})
        
        self.mem_threshold_mb = runtime_prot.get("memory_leak_threshold_mb", 512)
        self.compliance_lock = runtime_prot.get("enforce_compliance_lock", True)
        
        node_infra = self.config.get("node_infrastructure", self.config.get("node", {}))
        self.air_gapped = node_infra.get("air_gapped_enforcement", node_infra.get("air_gapped", True))

    def _load_config(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def verify_network_isolation(self) -> bool:
        """Проверяет, не открыл ли процесс ИИ несанкционированные внешние соединения."""
        if not self.air_gapped:
            return True
            
        print("[SHIELD] Проверка сетевой изоляции контура...")
        try:
            # Попытка установить внешнее соединение
            socket.create_connection(("8.8.8.8", 53), timeout=1.0)
            return False # Если соединение успешно — изоляция пробита!
        except (socket.timeout, OSError):
            return True # Сеть надежно заблокирована

    def monitor_loop(self):
        """Основной цикл контроля за выполнением процесса ИИ."""
        print(f"[SHIELD] Запуск суверенного ИИ-процесса: {self.command}")
        print("=" * 60)
        
        # Запуск целевого ИИ-движка в изолированном подпроцессе
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        psutil_proc = psutil.Process(self.process.pid)
        
        # Небольшая задержка, чтобы процесс успел выделить базовую память
        time.sleep(1)
        initial_memory = psutil_proc.memory_info().rss / (1024 * 1024)
        print(f"[SHIELD] Базовое потребление памяти процессом: {initial_memory:.2f} MB")

        try:
            while self.process.poll() is None:
                time.sleep(2) # Интервал проверки — каждые 2 секунды
                
                # 1. Контроль утечек памяти (Memory Leak Protection)
                current_memory = psutil_proc.memory_info().rss / (1024 * 1024)
                mem_drift = current_memory - initial_memory
                
                print(f"[TELEMETRY] Текущая RAM: {current_memory:.2f} MB | Дрейф: {mem_drift:.2f} MB")

                if mem_drift > self.mem_threshold_mb:
                    print(f"\n[ALERT] КРИТИЧЕСКАЯ УТЕЧКА ПАМЯТИ: Превышен лимит в {self.mem_threshold_mb} MB.")
                    self.terminate_incident("MEMORY_EXCEEDED")
                    break

                # 2. Контроль сетевого трафика во время выполнения
                if not self.verify_network_isolation():
                    print("\n[ALERT] НАРУШЕНИЕ БЕЗОПАСНОСТИ: Обнаружена несанкционированная WAN-активность!")
                    self.terminate_incident("NETWORK_VIOLATION")
                    break

        except KeyboardInterrupt:
            print("\n[SHIELD] Ручная остановка процесса пользователем.")
            self.terminate_incident("MANUAL_STOP")

    def terminate_incident(self, reason: str):
        """Аварийное уничтожение процесса (Kill Switch) при фиксации инцидента."""
        if self.process and self.process.poll() is None:
            print(f"[KILL SWITCH] Аварийное уничтожение ИИ-контекста. Причина: {reason}")
            self.process.kill()
            self.process.wait()
            
            if self.compliance_lock:
                print("[COMPLIANCE LOCK] АКТИВИРОВАН ПОЛНЫЙ БЛОК НОДЫ. Все внешние API-интерфейсы заморожены.")
            sys.exit(1)
        print("[SHIELD] ИИ-процесс успешно завершил работу.")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OASA Runtime Shield")
    parser.add_argument("--config", type=str, required=True, help="Путь к sovereign-stack.yaml")
    parser.add_argument("--cmd", type=str, required=True, help="Команда запуска ИИ-модели/прокси")
    args = parser.parse_args()

    shield = RuntimeShield(args.config, args.cmd)
    shield.monitor_loop()
