# Based on UPS Lite v1.1 from https://github.com/xenDE
#
# functions for get UPS status - needs enable "i2c" in raspi-config
#
# https://github.com/linshuqin329/UPS-Lite
#
# For Raspberry Pi Zero Ups Power Expansion Board with Integrated Serial Port S3U4
# https://www.ebay.de/itm/For-Raspberry-Pi-Zero-Ups-Power-Expansion-Board-with-Integrated-Serial-Port-S3U4/323873804310
# https://www.aliexpress.com/item/32888533624.html
import logging
import struct

from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
from pwnagotchi.ui import fonts
from pwnagotchi import plugins
import pwnagotchi


class UPS:
    def __init__(self):
        # only import when the module is loaded and enabled
        import smbus

        # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
        self._bus = smbus.SMBus(1)

    def voltage(self):
        try:
            address = 0x36
            read = self._bus.read_word_data(address, 2)
            swapped = struct.unpack("<H", struct.pack(">H", read))[0]
            return swapped * 1.25 / 1000 / 16
        except Exception as ex:
            logging.error("[upslite] %s", ex)
            return 0.0

    def capacity(self):
        try:
            address = 0x36
            read = self._bus.read_word_data(address, 4)
            swapped = struct.unpack("<H", struct.pack(">H", read))[0]
            return swapped / 256
        except Exception as ex:
            logging.error("[upslite] %s", ex)
            return 0.0


class UPSLite(plugins.Plugin):
    __author__ = "evilsocket@gmail.com"
    __version__ = "2.0.0"
    __license__ = "GPL3"
    __description__ = "A plugin that will add a voltage indicator for the UPS Lite v1.1"
    __name__ = "UPSLite"
    __help__ = "A plugin that will add a voltage indicator for the UPS Lite v1.1"
    __dependencies__ = {
        "pip": ["scapy"],
    }
    __defaults__ = {
        "enabled": False,
    }

    def __init__(self):
        self.ups = None

    def on_loaded(self):
        self.ups = UPS()

    def on_ui_setup(self, ui):
        ui.add_element(
            "ups",
            LabeledValue(
                color=BLACK,
                label="UPS",
                value="0%/0V",
                position=(ui.width() / 2 + 15, 0),
                label_font=fonts.Bold,
                text_font=fonts.Medium,
            ),
        )

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element("ups")

    def on_ui_update(self, ui):
        capacity = self.ups.capacity()
        ui.set("ups", "%2i%%" % capacity)
        if capacity <= self.options["shutdown"]:
            logging.info(
                "[upslite] Empty battery (<= %s%%): shuting down"
                % self.options["shutdown"]
            )
            ui.update(force=True, new_data={"status": "Battery exhausted, bye ..."})
            pwnagotchi.shutdown()
