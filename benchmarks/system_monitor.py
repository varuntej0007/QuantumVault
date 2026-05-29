"""
System resource monitor during crypto operations.
Captures: CPU%, RAM MB, CPU temp°C, estimated power draw
Runs alongside benchmarks to show edge deployment viability.
"""
import time, json, threading, subprocess
from datetime import datetime


def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000.0
    except:
        return 0.0


def get_ram_mb():
    import psutil
    return psutil.Process().memory_info().rss / 1e6


def get_cpu_percent():
    import psutil
    return psutil.cpu_percent(interval=0.1)


class SystemMonitor:
    """Run in background thread during benchmarks."""
    def __init__(self, interval=0.5):
        self.interval = interval
        self.readings = []
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._collect)
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread.join()

    def _collect(self):
        while self._running:
            self.readings.append({
                "timestamp": time.time(),
                "cpu_percent": get_cpu_percent(),
                "ram_mb": get_ram_mb(),
                "temp_c": get_cpu_temp(),
            })
            time.sleep(self.interval)

    def summary(self):
        if not self.readings:
            return {}
        cpus = [r["cpu_percent"] for r in self.readings]
        temps = [r["temp_c"] for r in self.readings]
        rams = [r["ram_mb"] for r in self.readings]
        return {
            "cpu_mean_pct": sum(cpus)/len(cpus),
            "cpu_max_pct": max(cpus),
            "temp_mean_c": sum(temps)/len(temps),
            "temp_max_c": max(temps),
            "ram_mean_mb": sum(rams)/len(rams),
            "ram_peak_mb": max(rams),
            "samples": len(self.readings)
        }
