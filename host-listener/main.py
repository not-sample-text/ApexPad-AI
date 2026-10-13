import threading
from core.config_manager import ConfigManager
from core.telemetry_manager import TelemetryManager
from core.serial_manager import SerialManager
from core.web_server import ApexWebServer
from ui.tray_icon import ApexTrayIcon
from utils.logger import get_logger

logger = get_logger("MainApp")


def main() -> None:
    logger.info("Booting ApexPad AI Background Daemon...")

    # 1. Initialize configuration and telemetry managers
    config_mgr = ConfigManager()
    config_mgr.locate_and_load()

    telemetry_mgr = TelemetryManager(config_mgr.base_dir)

    # 2. Initialize Serial Manager and start background listener thread
    serial_mgr = SerialManager(config_mgr, telemetry_mgr)
    listener_thread = threading.Thread(target=serial_mgr.start_daemon, daemon=True)
    listener_thread.start()

    # 3. Start lightweight local HTTP & API server for the Web Configurator
    web_server = ApexWebServer(config_mgr, serial_mgr, telemetry_mgr)
    web_server.start_background()

    # 4. Launch System Tray Icon on the main thread (Blocking)
    tray = ApexTrayIcon(serial_mgr, config_mgr, web_server)
    tray.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Exiting gracefully.")
