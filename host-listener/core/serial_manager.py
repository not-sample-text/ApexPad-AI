import re
import time
import json
import serial
import serial.tools.list_ports
from typing import Any
from utils.logger import get_logger
from handlers.execution_handler import ExecutionHandler

logger = get_logger("SerialManager")

KEY_PRESS_RE = re.compile(r"\[EVENT\]\s*Key Pressed\s*-\s*Layer:\s*(\d+),\s*Row:\s*(\d+),\s*Col:\s*(\d+)")
LAYER_SWITCH_RE = re.compile(r"\[LOG\]\s*Switched to Layer\s*(\d+)")


class SerialManager:
    def __init__(self, config_manager: Any, telemetry_manager: Any = None) -> None:
        self.config_manager = config_manager
        self.telemetry_manager = telemetry_manager
        self.serial_conn: serial.Serial | None = None
        self.is_running = False
        self.connected_port: str | None = None
        self.last_sync_status: str = "IDLE"

        self._wants_upload = False
        self._wants_download = False
        self._force_dump = False

    def is_connected(self) -> bool:
        return bool(self.serial_conn and self.serial_conn.is_open)

    def get_status(self) -> dict[str, Any]:
        return {
            "connected": self.is_connected(),
            "port": self.connected_port if self.is_connected() else None,
            "sync_status": self.last_sync_status
        }

    def auto_connect(self) -> None:
        while self.is_running:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                try:
                    s = serial.Serial(port.device, 115200, timeout=1)
                    time.sleep(0.1)
                    s.write(b"[PING]\n")
                    time.sleep(0.1)

                    response = s.read_all().decode("utf-8", errors="ignore")
                    if "[PONG:APEXPAD]" in response:
                        logger.info(f"ApexPad established on {port.device}!")
                        self.serial_conn = s
                        self.connected_port = port.device
                        return
                    s.close()
                except Exception:
                    pass

            time.sleep(3)

    def start_daemon(self) -> None:
        self.is_running = True

        while self.is_running:
            if not self.serial_conn or not self.serial_conn.is_open:
                self.connected_port = None
                self.auto_connect()
                if not self.is_running:
                    break

            if self._wants_upload:
                self._wants_upload = False
                self._execute_upload()
                continue

            if self._wants_download:
                self._wants_download = False
                logger.info("Requesting hardware config...")
                self.last_sync_status = "DOWNLOADING"
                try:
                    self.serial_conn.write(b"[CFG_READ_REQ]\n")
                except Exception as e:
                    logger.error(f"Failed to request config read: {e}")
                    self.last_sync_status = "ERROR"
                continue

            try:
                line = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                if line.startswith("[CMD:") and line.endswith("]"):
                    hex_str = line[5:-1]
                    self._handle_cmd(hex_str)
                    continue  # FIX: Prevent fall-through double execution

                elif "[CFG_READ_START]" in line:
                    self._read_downloaded_config()
                    continue

                elif line.startswith("[EVENT]") or line.startswith("[LOG]") or line.startswith("[SYSTEM]"):
                    logger.info(f"Hardware: {line}")
                    self._parse_telemetry_line(line)
                    continue

                elif line:
                    logger.debug(f"Hardware (Raw): {line}")

            except serial.SerialException:
                logger.error("Serial connection lost. Reverting to discovery mode...")
                self.connected_port = None
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Listener loop exception: {e}")
        self.is_running = True

        while self.is_running:
            if not self.serial_conn or not self.serial_conn.is_open:
                self.connected_port = None
                self.auto_connect()
                if not self.is_running:
                    break

            if self._wants_upload:
                self._wants_upload = False
                self._execute_upload()
                continue

            if self._wants_download:
                self._wants_download = False
                logger.info("Requesting hardware config...")
                self.last_sync_status = "DOWNLOADING"
                try:
                    self.serial_conn.write(b"[CFG_READ_REQ]\n")
                except Exception as e:
                    logger.error(f"Failed to request config read: {e}")
                    self.last_sync_status = "ERROR"

            try:
                line = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                if line.startswith("[CMD:") and line.endswith("]"):
                    hex_str = line[5:-1]
                    self._handle_cmd(hex_str)

                elif "[CFG_READ_START]" in line:
                    self._read_downloaded_config()

                # FIX: Upgraded to logger.info to guarantee UI propagation
                elif line.startswith("[EVENT]") or line.startswith("[LOG]") or line.startswith("[SYSTEM]"):
                    logger.info(f"Hardware: {line}")
                    self._parse_telemetry_line(line)

                else:
                    logger.debug(f"Hardware (Raw): {line}")

            except serial.SerialException:
                logger.error("Serial connection lost. Reverting to discovery mode...")
                self.connected_port = None
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Listener loop exception: {e}")
        self.is_running = True

        while self.is_running:
            if not self.serial_conn or not self.serial_conn.is_open:
                self.connected_port = None
                self.auto_connect()
                if not self.is_running:
                    break

            if self._wants_upload:
                self._wants_upload = False
                self._execute_upload()
                continue

            if self._wants_download:
                self._wants_download = False
                logger.info("Requesting hardware config...")
                self.last_sync_status = "DOWNLOADING"
                try:
                    self.serial_conn.write(b"[CFG_READ_REQ]\n")
                except Exception as e:
                    logger.error(f"Failed to request config read: {e}")
                    self.last_sync_status = "ERROR"

            try:
                line = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                if line.startswith("[CMD:") and line.endswith("]"):
                    hex_str = line[5:-1]
                    self._handle_cmd(hex_str)

                elif "[CFG_READ_START]" in line:
                    self._read_downloaded_config()

                elif line.startswith("[EVENT]") or line.startswith("[LOG]") or line.startswith("[SYSTEM]"):
                    logger.debug(f"Hardware: {line}")
                    self._parse_telemetry_line(line)

                else:
                    logger.debug(f"Hardware (Raw): {line}")

            except serial.SerialException:
                logger.error("Serial connection lost. Reverting to discovery mode...")
                self.connected_port = None
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Listener loop exception: {e}")

    def _parse_telemetry_line(self, line: str) -> None:
        if not self.telemetry_manager:
            return

        kp_match = KEY_PRESS_RE.search(line)
        if kp_match:
            layer = int(kp_match.group(1))
            row = int(kp_match.group(2))
            col = int(kp_match.group(3))
            self.telemetry_manager.record_keypress(layer, row, col)
            return

        ls_match = LAYER_SWITCH_RE.search(line)
        if ls_match:
            new_layer = int(ls_match.group(1))
            self.telemetry_manager.record_layer_switch(new_layer)

    def stop_daemon(self) -> None:
        self.is_running = False
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass

    def _handle_cmd(self, hex_str: str) -> None:
        try:
            packed = int(hex_str, 16)
            layer = packed >> 4
            key_index = packed & 0x0F
            
            # FIX: Unpack matching the C++ (row * 3) + col logic
            row = key_index // 3
            col = key_index % 3

            logger.info(f"Intercepted Command -> Layer: {layer}, Row: {row}, Col: {col}")
            action = self.config_manager.get_action(layer, row, col)
            if action:
                ExecutionHandler.execute(action)
            else:
                logger.warning(f"No valid action mapped for Key C{col}R{row} on Layer {layer}.")
        except ValueError:
            pass
        try:
            packed = int(hex_str, 16)
            layer = packed >> 4
            key_index = (packed & 0x0F) - 1
            col = key_index // 4
            row = key_index % 4

            logger.info(f"Intercepted Command -> Layer: {layer}, Row: {row}, Col: {col}")
            action = self.config_manager.get_action(layer, row, col)
            if action:
                ExecutionHandler.execute(action)
            else:
                logger.warning(f"No valid action mapped for Key C{col}R{row} on Layer {layer}.")
        except ValueError:
            pass
        try:
            packed = int(hex_str, 16)
            layer = packed >> 4
            key_index = (packed & 0x0F) - 1
            col = key_index // 4
            row = key_index % 4

            # FIX: Upgraded to logger.info
            logger.info(f"Intercepted Command -> Layer: {layer}, Row: {row}, Col: {col}")
            action = self.config_manager.get_action(layer, row, col)
            if action:
                ExecutionHandler.execute(action)
            else:
                logger.warning(f"No valid action mapped for Key C{col}R{row} on Layer {layer}.")
        except ValueError:
            pass
        try:
            packed = int(hex_str, 16)
            layer = packed >> 4
            key_index = (packed & 0x0F) - 1
            col = key_index // 4
            row = key_index % 4

            logger.debug(f"Intercepted Command -> Layer: {layer}, Row: {row}, Col: {col}")
            action = self.config_manager.get_action(layer, row, col)
            if action:
                ExecutionHandler.execute(action)
            else:
                logger.warning(f"No valid action mapped for Key C{col}R{row} on Layer {layer}.")
        except ValueError:
            pass

    def trigger_config_upload(self) -> bool:
        if not self.is_connected():
            logger.error("Cannot queue upload: ApexPad is not connected over USB Serial.")
            self.last_sync_status = "DISCONNECTED"
            return False
        self.last_sync_status = "QUEUED"
        self._wants_upload = True
        return True

    def trigger_config_download(self) -> bool:
        if not self.is_connected():
            logger.error("Cannot recover config: ApexPad is not connected.")
            return False
        self._wants_download = True
        self._force_dump = False
        return True

    def trigger_force_dump(self) -> bool:
        if not self.is_connected():
            logger.error("Cannot force dump: ApexPad is not connected.")
            return False
        self._wants_download = True
        self._force_dump = True
        return True

    def _execute_upload(self) -> None:
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("Upload aborted: No active connection.")
            self.last_sync_status = "ERROR"
            return

        self.last_sync_status = "UPLOADING"
        logger.info("Initiating upload protocol...")
        self.serial_conn.write(b"[CFG_WRITE_REQ]\n")

        ack_wait_start = time.time()
        ack_received = False
        while time.time() - ack_wait_start < 3.0:
            line = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
            if "[CFG_WRITE_ACK]" in line:
                ack_received = True
                break

        if not ack_received:
            logger.error("Timeout: Hardware failed to ACK.")
            self.last_sync_status = "ERROR"
            return

        json_str = self.config_manager.get_raw_json_string()
        lines = json_str.splitlines()

        delay = min(0.008, 3.5 / len(lines)) if lines else 0.005

        upload_start = time.time()
        for line in lines:
            if time.time() - upload_start > 4.5:
                logger.error("Upload aborted: Exceeded strict 5-second time limit.")
                self.last_sync_status = "ERROR"
                return
            self.serial_conn.write((line + "\n").encode("utf-8"))
            time.sleep(delay)

        self.serial_conn.write(b"\n[CFG_WRITE_EOF]\n")
        logger.info("Payload sent. Waiting for hardware hot-reload confirmation...")

        confirm_start = time.time()
        while time.time() - confirm_start < 3.0:
            resp = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
            if not resp:
                continue
            logger.debug(f"Hardware: {resp}")
            if "[CFG_WRITE_OK]" in resp:
                logger.info("Hardware configuration hot-reloaded successfully!")
                self.last_sync_status = "SUCCESS"
                return
            if "[CFG_WRITE_ERR]" in resp:
                logger.error("Hardware rejected configuration and rolled back.")
                self.last_sync_status = "ERROR"
                return

        logger.info("Upload finished.")
        self.last_sync_status = "SUCCESS"

    def _read_downloaded_config(self) -> None:
        logger.info("Hardware initiated config recovery stream...")
        buffer: list[str] = []
        timeout_start = time.time()
        max_lines = 1000

        while time.time() - timeout_start < 5.0 and len(buffer) < max_lines:
            line = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
            if "[CFG_READ_END]" in line:
                break
            if line:
                buffer.append(line)

        if not buffer:
            logger.warning("Hardware returned an empty configuration.")
            self.last_sync_status = "ERROR"
            return

        json_str = "\n".join(buffer)

        if self._force_dump:
            logger.info("Emergency Dump flag active. Bypassing schema validation...")
            self.config_manager.dump_config_to_desktop(json_str)
            self._force_dump = False
            self.last_sync_status = "DUMP_SUCCESS"
            return

        try:
            parsed = json.loads(json_str)
            if "layers" not in parsed or not isinstance(parsed["layers"], list):
                logger.error("Hardware provided invalid config schema. Rejecting.")
                self.last_sync_status = "ERROR"
                return

            self.config_manager.save_recovered_config(json_str)
            self.last_sync_status = "RECOVER_SUCCESS"
        except json.JSONDecodeError as e:
            logger.error("Hardware provided malformed JSON. Rejecting.")
            logger.error(f"Parse Error Details: {e.msg} at Line {e.lineno}, Column {e.colno}")
            self.last_sync_status = "ERROR"
