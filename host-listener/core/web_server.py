import json
import os
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from typing import Any
from utils.logger import get_logger, get_logs_since, clear_logs

logger = get_logger("WebServer")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def get_web_root() -> str:
    """Resolves the web-configurator directory for both source and PyInstaller builds."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(getattr(sys, "_MEIPASS"), "web-configurator")
    host_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_root = os.path.dirname(host_dir)
    return os.path.join(repo_root, "web-configurator")


class ApexHttpRequestHandler(SimpleHTTPRequestHandler):
    server_version = "ApexPadHTTP/1.0"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=get_web_root(), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy static file HTTP access logs in the debug console
        pass

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="ignore")
        return json.loads(raw) if raw else {}

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        app_server: "ApexWebServer" = self.server.app_ref  # type: ignore[attr-defined]

        if path == "/api/status":
            status = app_server.serial_mgr.get_status()
            telemetry = app_server.telemetry_mgr.get_telemetry()
            status["total_keypresses"] = telemetry.get("total_keypresses", 0)
            status["layer_switches"] = telemetry.get("layer_switches", 0)
            self._send_json(200, status)
            return

        if path == "/api/config":
            self._send_json(200, app_server.config_mgr.get_config_dict())
            return

        if path == "/api/telemetry":
            self._send_json(200, app_server.telemetry_mgr.get_telemetry())
            return

        if path == "/api/logs":
            qs = parse_qs(parsed.query)
            since_id = int(qs.get("since", ["0"])[0])
            logs = get_logs_since(since_id)
            self._send_json(200, {"logs": logs})
            return

        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        app_server: "ApexWebServer" = self.server.app_ref  # type: ignore[attr-defined]

        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON body: {e}"})
            return

        if path == "/api/config":
            config_payload = body.get("config", body)
            saved = app_server.config_mgr.save_config_from_web(config_payload)
            if saved:
                self._send_json(200, {"ok": True, "config": app_server.config_mgr.get_config_dict()})
            else:
                self._send_json(400, {"ok": False, "error": "Failed to validate or save configuration."})
            return

        if path == "/api/upload":
            config_payload = body.get("config")
            if isinstance(config_payload, dict) and "layers" in config_payload:
                if not app_server.config_mgr.save_config_from_web(config_payload):
                    self._send_json(400, {"ok": False, "error": "Invalid configuration structure."})
                    return

            queued = app_server.serial_mgr.trigger_config_upload()
            if queued:
                self._send_json(200, {"ok": True, "message": "Upload queued to ApexPad over serial."})
            else:
                self._send_json(503, {"ok": False, "error": "ApexPad is not connected over USB Serial."})
            return

        if path == "/api/recover":
            ok = app_server.serial_mgr.trigger_config_download()
            if ok:
                self._send_json(200, {"ok": True, "message": "Requested configuration recovery from ApexPad."})
            else:
                self._send_json(503, {"ok": False, "error": "ApexPad is not connected."})
            return

        if path == "/api/force-dump":
            ok = app_server.serial_mgr.trigger_force_dump()
            if ok:
                self._send_json(200, {"ok": True, "message": "Emergency dump requested (saving to Desktop)."})
            else:
                self._send_json(503, {"ok": False, "error": "ApexPad is not connected."})
            return

        if path == "/api/logs/clear":
            clear_logs()
            self._send_json(200, {"ok": True})
            return

        if path == "/api/telemetry/reset":
            app_server.telemetry_mgr.reset()
            self._send_json(200, {"ok": True})
            return

        if path == "/api/optimize":
            try:
                from ai.orchestrator import optimize_layout
                prompt = str(body.get("prompt", "")).strip()
                layer_id = body.get("layer_id")
                model_name = str(body.get("model", "llama3.2")).strip() or "llama3.2"
                current_cfg = body.get("config") or app_server.config_mgr.get_config_dict()
                telemetry = app_server.telemetry_mgr.get_telemetry()

                result = optimize_layout(
                    prompt=prompt,
                    current_config=current_cfg,
                    telemetry=telemetry,
                    target_layer_id=layer_id,
                    model_name=model_name
                )
                self._send_json(200, result)
            except ImportError:
                self._send_json(501, {
                    "ok": False,
                    "error": "AI optimization module (host-listener/ai/) is not installed yet."
                })
            except Exception as e:
                logger.error(f"AI Optimization error: {e}")
                self._send_json(500, {"ok": False, "error": str(e)})
            return

        self._send_json(404, {"ok": False, "error": f"Unknown endpoint: {path}"})


class ApexWebServer:
    def __init__(
        self,
        config_mgr: Any,
        serial_mgr: Any,
        telemetry_mgr: Any,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT
    ) -> None:
        self.config_mgr = config_mgr
        self.serial_mgr = serial_mgr
        self.telemetry_mgr = telemetry_mgr
        self.host = host
        self.port = port
        self._httpd: ThreadingHTTPServer | None = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start_background(self) -> None:
        self._httpd = ThreadingHTTPServer((self.host, self.port), ApexHttpRequestHandler)
        self._httpd.app_ref = self  # type: ignore[attr-defined]
        thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Web Configurator server listening at {self.url}")

    def open_in_browser(self) -> None:
        webbrowser.open(self.url)

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
