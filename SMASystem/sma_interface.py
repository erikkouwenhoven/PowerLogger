"""
    https://github.com/Dymerz/SMA-SunnyBoy
    https://sma-sunnyboy.readthedocs.io/en/latest/sma_sunnyboy.html
"""

import time
import logging
from enum import Enum, auto
from SMASystem.sma import WebConnect
from SMASystem.key import Key
from SMASystem.right import Right
from Utils.settings import Settings


class SMADataType(Enum):

    SOLAR = auto()


class SMAInterface:
    """
        Interface to the SMA Sunny Boy web server.
    """

    c_POWER_UNIT = 'W'

    def __init__(self):
        self.client = self.initConnection()

    @staticmethod
    def initConnection():
        client = WebConnect(Settings().smaHostname(), Right.USER, Settings().smaPassword())
        result = client.auth()
        if result is True:
            logging.info(f"Initializing connection to SMA Interface: success")
            return client
        else:
            logging.warning("Failed to initialize SMA interface")

    def getCurrentPower(self):
        self.validateConnection()
        if self.client:
            return self.client.get_value(Key.power_current)

    def getTotal(self):
        self.validateConnection()
        if self.client:
            return self.client.get_value(Key.productivity_total)

    def getHistory(self, time_in_seconds):
        self.validateConnection()
        if self.client:
            now_time = int(time.time())
            return self.client.get_logger(now_time - time_in_seconds, now_time)

    def validateConnection(self):
        if self.client:
            if self.client.check_connection() is False:
                logging.error("SMA interface connection check failed")
                self.client = self.initConnection()
        else:
            self.client = self.initConnection()

    def __del__(self):
        if self.client:
            self.client.logout()


if __name__ == "__main__":
    smaInterface = SMAInterface()
    print(f"SMA power: {smaInterface.getCurrentPower()}")
    print(f"SMA keys: {smaInterface.client.get_all_keys()}")
