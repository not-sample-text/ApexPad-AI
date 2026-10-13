import json
import os
import sys
import threading
import time
from typing import Any
from utils.logger import get_logger

logger = get_logger("TelemetryManager")

# Maximum elapsed seconds between two presses to count as a sequential transition
TRANSITION_WINDOW_SEC = 15.0


class TelemetryManager:
    def __init__(self, base_dir: str | None = None) -> None:
        if base_dir is None:
            if getattr(sys, "frozen", False):
                base_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.telemetry_path = os.path.join(base_dir, "telemetry.json")
        self._lock = threading.Lock()

        self.data: dict[str, Any] = self._default_data()
        self._last_layer: int | None = None
        self._last_coord: str | None = None
        self._last_press_time: float = 0.0
        self._pending_layer_switch_from: tuple[int, str] | None = None

        self.load()

    @staticmethod
    def _default_data() -> dict[str, Any]:
        return {
            "key_counts": {
                "0": {},
                "1": {},
                "2": {},
                "3": {}
            },
            "intra_layer_transitions": {
                "0": {},
                "1": {},
                "2": {},
                "3": {}
            },
            "cross_layer_transitions": {},
            "layer_switches": 0,
            "total_keypresses": 0
        }

    def load(self) -> None:
        with self._lock:
            if os.path.exists(self.telemetry_path):
                try:
                    with open(self.telemetry_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, dict) and "key_counts" in loaded:
                        self.data = loaded
                        logger.info("Loaded telemetry.json into memory.")
                        return
                except Exception as e:
                    logger.warning(f"Failed to read telemetry.json, starting fresh: {e}")

            self.data = self._default_data()
            self._save_unlocked()

    def _save_unlocked(self) -> None:
        try:
            with open(self.telemetry_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save telemetry.json: {e}")

    def record_layer_switch(self, new_layer: int) -> None:
        now = time.time()
        with self._lock:
            self.data["layer_switches"] = self.data.get("layer_switches", 0) + 1
            if (
                self._last_layer is not None
                and self._last_coord is not None
                and self._last_layer != new_layer
                and (now - self._last_press_time) <= TRANSITION_WINDOW_SEC
            ):
                self._pending_layer_switch_from = (self._last_layer, self._last_coord)
            self._save_unlocked()

    def record_keypress(self, layer: int, row: int, col: int) -> None:
        coord = f"C{col}R{row}"
        layer_key = str(layer)
        now = time.time()

        with self._lock:
            self.data["total_keypresses"] = self.data.get("total_keypresses", 0) + 1

            # 1. Increment raw key count
            layer_counts = self.data["key_counts"].setdefault(layer_key, {})
            layer_counts[coord] = layer_counts.get(coord, 0) + 1

            # 2. Record Intra-Layer Transition (X/Y axis)
            if (
                self._last_layer == layer
                and self._last_coord is not None
                and self._last_coord != coord
                and (now - self._last_press_time) <= TRANSITION_WINDOW_SEC
            ):
                pair_key = f"{self._last_coord}->{coord}"
                intra_map = self.data["intra_layer_transitions"].setdefault(layer_key, {})
                intra_map[pair_key] = intra_map.get(pair_key, 0) + 1

            # 3. Record Cross-Layer Transition (Z-axis across EC11 switch)
            if self._pending_layer_switch_from is not None:
                prev_layer, prev_coord = self._pending_layer_switch_from
                if prev_layer != layer and (now - self._last_press_time) <= TRANSITION_WINDOW_SEC:
                    cross_key = f"L{prev_layer}:{prev_coord}->L{layer}:{coord}"
                    cross_map = self.data.setdefault("cross_layer_transitions", {})
                    cross_map[cross_key] = cross_map.get(cross_key, 0) + 1
                self._pending_layer_switch_from = None

            self._last_layer = layer
            self._last_coord = coord
            self._last_press_time = now

            self._save_unlocked()

    def get_telemetry(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self.data))

    def reset(self) -> None:
        with self._lock:
            self.data = self._default_data()
            self._last_layer = None
            self._last_coord = None
            self._last_press_time = 0.0
            self._pending_layer_switch_from = None
            self._save_unlocked()
            logger.info("Telemetry data reset by user.")
