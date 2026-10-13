import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from typing import Any
from utils.logger import get_logger

logger = get_logger("TrayIcon")


class ApexTrayIcon:
    def __init__(self, serial_mgr: Any, config_mgr: Any, web_server: Any) -> None:
        self.serial_mgr = serial_mgr
        self.config_mgr = config_mgr
        self.web_server = web_server
        self.icon: pystray.Icon | None = None

    @staticmethod
    def _create_image() -> Image.Image:
        image = Image.new("RGB", (64, 64), color=(18, 24, 38))
        dc = ImageDraw.Draw(image)
        dc.rectangle((8, 8, 56, 56), outline=(0, 229, 255), width=4)
        dc.rectangle((22, 22, 42, 42), fill=(0, 229, 255))
        return image

    def _on_open_configurator(self, icon: Any, menu_item: Any) -> None:
        logger.info("Opening ApexPad Web Configurator in browser...")
        self.web_server.open_in_browser()

    def _on_exit(self, icon: Any, menu_item: Any) -> None:
        logger.info("Shutting down ApexPad Daemon...")
        self.serial_mgr.stop_daemon()
        self.web_server.stop()
        if self.icon:
            self.icon.stop()

    def run(self) -> None:
        menu = pystray.Menu(
            item("Open Configurator", self._on_open_configurator, default=True),
            pystray.Menu.SEPARATOR,
            item("Exit", self._on_exit)
        )

        self.icon = pystray.Icon("ApexPad", self._create_image(), "ApexPad AI", menu)
        self.icon.run()
