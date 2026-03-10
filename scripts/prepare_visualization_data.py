import json
from pathlib import Path
from typing import Dict, List


class DataHandler:
    def __init__(
        self,
        data: List[Dict] = None,
        path: Path = Path(
            Path(__file__).parent.parent.absolute() / "assets/experiment_results"
        ),
    ):
        self.path = path
        self.data = data
        self.timedata = []
        self.memdata = []
        self.clients = []
        self.peak_mem = []

    def __enter__(self):
        if not self.data:
            self.load_experiment_results()

    @property
    def time_series(self):
        for test in self.data:
            avg_time = test["resources"].get("duration_seconds", None)
            if avg_time:
                self.timedata.append(float(f"{avg_time:.2f}"))
                continue
            timedata = test["resources"]["timestamps"]
            time_difference = timedata[1] - timedata[0]
            self.timedata.append(float(f"{time_difference:.2f}"))
        return self.timedata

    @property
    def memory_series(self):
        for test in self.data:
            memdata = test["resources"]["memory_usage_mb"]
            memory_difference = memdata[1] - memdata[0]
            self.memdata.append(memory_difference)
        return self.memdata

    @property
    def peak_memory_series(self):
        for test in self.data:
            peak_mem = test["resources"]["max_memory_mb"]
            self.peak_mem.append(peak_mem)
        return self.peak_mem

    @property
    def client_series(self):
        for test in self.data:
            clients = test["num_clients"]
            self.clients.append(clients)
        return self.clients

    @property
    def timestamp_series(self):
        return [float(f"{t['resources']['timestamps'][0]:.2f}") for t in self.data]

    @property
    def cpu_percent_series(self):
        return [
            float(f"{t['resources']['average_cpu_percent']:.2f}") for t in self.data
        ]

    @property
    def round_per_min(self):
        """
        formula = target * rounds / time
        target = i min = 60 seconds
        rounds = 1
        time= time take for one round
        fm = target/time
        """
        timedata = self.time_series
        return [float(f"{(60 / t):.2f}") for t in timedata]

    def dummy_accuracy_series(self, size: int):
        import random

        return [random.randint(85, 97) for i in range(size)]

    def get_all_series(self) -> dict:
        return {
            "time": self.time_series,
            "memory": self.memory_series,
            "peak_memory": self.peak_memory_series,
            "clients": self.client_series,
            "accuracy": self.dummy_accuracy_series(len(self.data)),
            "timestamps": self.timestamp_series,
            "cpu_percent": self.cpu_percent_series,
            "round_per_min": self.round_per_min,
        }

    def load_experiment_results(self, path: Path) -> List[Dict]:
        """Load experiment results from directory."""
        results = {}
        self.path = path
        if not self.path:
            raise Exception("Experiements pat not provided")

        # Look for JSON files
        for file_path in path.rglob("*.json"):
            if file_path.name.endswith("results.json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                    results[file_path.stem] = data
        self.data = results.get("dashboard_integration_results", None) or results
        return self.data
