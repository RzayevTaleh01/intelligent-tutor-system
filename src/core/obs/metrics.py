import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("eduvision")

class Metrics:
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)

    def inc(self, name: str, labels: Dict[str, str] = {}):
        key = f"{name}{str(labels)}"
        self.counters[key] += 1

    def observe(self, name: str, value: float, labels: Dict[str, str] = {}):
        key = f"{name}{str(labels)}"
        self.histograms[key].append(value)

    def get_prometheus_text(self) -> str:
        lines = []
        for key, val in self.counters.items():
            # Simplify for now
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {val}")
        return "\n".join(lines)

from collections import defaultdict
metrics = Metrics()
