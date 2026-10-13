import os
import sys
import json
import pathlib
from typing import Any
from utils.logger import get_logger

logger = get_logger("ConfigManager")


class ConfigManager:
    def __init__(self, base_dir: str | None = None) -> None:
        if base_dir is None:
            if getattr(sys, "frozen", False):
                base_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.base_dir = base_dir
        self.config_data: dict[str, Any] = {}
        self.local_config_path = os.path.join(self.base_dir, "config.json")

    def locate_and_load(self) -> None:
        if os.path.exists(self.local_config_path):
            self._load_json(self.local_config_path)
        else:
            logger.warning("No local config.json found. Initializing default structure...")
            self.config_data = {"layers": []}

    def _backup_local(self) -> None:
        """Renames the existing local config to config_old.json."""
        if os.path.exists(self.local_config_path):
            old_path = os.path.join(self.base_dir, "config_old.json")
            try:
                if os.path.exists(old_path):
                    os.remove(old_path)
                os.rename(self.local_config_path, old_path)
                logger.info("Backed up previous local config to config_old.json")
            except Exception as e:
                logger.error(f"Failed to backup old config: {e}")

    @staticmethod
    def _sanitize_config(data: dict[str, Any]) -> dict[str, Any]:
        """Strips deprecated lighting blocks and ensures layer structure integrity."""
        if isinstance(data, dict) and "lighting" in data:
            data = {k: v for k, v in data.items() if k != "lighting"}
        return data

    def save_config_from_web(self, new_config: dict[str, Any]) -> bool:
        """Saves a validated config dictionary from the Web UI to local config.json."""
        if not isinstance(new_config, dict) or "layers" not in new_config:
            logger.error("Invalid configuration payload received from Web UI.")
            return False

        sanitized = self._sanitize_config(new_config)
        self._backup_local()

        try:
            with open(self.local_config_path, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, indent=2)
            self.config_data = sanitized
            logger.info("Saved new configuration from Web UI to local config.json.")
            return True
        except Exception as e:
            logger.error(f"Failed to write local config.json: {e}")
            return False

    def save_recovered_config(self, json_str: str) -> None:
        """Backs up local, saves hardware-recovered config locally & in Downloads."""
        try:
            parsed = self._sanitize_config(json.loads(json_str))
            formatted_str = json.dumps(parsed, indent=2)
        except Exception:
            formatted_str = json_str

        self._backup_local()

        try:
            with open(self.local_config_path, "w", encoding="utf-8") as f:
                f.write(formatted_str)
            logger.info("Saved recovered config to local directory.")
        except Exception as e:
            logger.error(f"Failed to write local config: {e}")

        downloads_path = os.path.join(pathlib.Path.home(), "Downloads", "config.json")
        try:
            with open(downloads_path, "w", encoding="utf-8") as f:
                f.write(formatted_str)
            logger.info(f"Saved duplicate to: {downloads_path}")
        except Exception as e:
            logger.error(f"Failed to write to Downloads: {e}")

        self._load_json(self.local_config_path)

    def dump_config_to_desktop(self, json_str: str) -> None:
        """Saves raw string from hardware to Desktop as emergency_dump.json."""
        desktop_path = os.path.join(pathlib.Path.home(), "Desktop", "emergency_dump.json")
        try:
            with open(desktop_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            logger.info(f"SUCCESS: Raw hardware dump securely written to {desktop_path}")
        except Exception as e:
            logger.error(f"Failed to write emergency dump to Desktop: {e}")

    def _load_json(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.config_data = self._sanitize_config(loaded)
            logger.info("Configuration successfully loaded into memory.")
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")

    def get_config_dict(self) -> dict[str, Any]:
        if not self.config_data:
            self.locate_and_load()
        return self.config_data

    def get_raw_json_string(self) -> str:
        if not os.path.exists(self.local_config_path):
            return json.dumps(self.config_data or {"layers": []})
        with open(self.local_config_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_action(self, layer_id: int, row: int, col: int) -> dict[str, Any] | None:
        if not self.config_data or "layers" not in self.config_data:
            return None

        key_id = f"C{col}R{row}"
        for layer in self.config_data["layers"]:
            if layer.get("id") == layer_id:
                keys = layer.get("keys", {})
                return keys.get(key_id)
        return None
