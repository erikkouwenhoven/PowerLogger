"""
    https://github.com/Dymerz/SMA-SunnyBoy
    https://sma-sunnyboy.readthedocs.io/en/latest/sma_sunnyboy.html
"""

import time
import logging
from sma_sunnyboy import *
from Utils.settings import Settings


class SMAInterface:
    """
        Interface to the SMA Sunny Boy web server.
    """

    c_POWER_UNIT = b'W'

    def __init__(self):
        self.client = self.initConnection()

    @staticmethod
    def initConnection():
        client = WebConnect(Settings().smaHostname(), Right.USER, Settings().smaPassword())
        result = client.auth()
        logging.info(f"Initializing connection to SMA Interface: {'success' if result is True else 'failure'}")
        return client

    def getCurrentPower(self):
        self.validateConnection()
        return self.client.get_value(Key.power_current)

    def getTotal(self):
        self.validateConnection()
        return self.client.get_value(Key.productivity_total)

    def getHistory(self, time_in_seconds):
        self.validateConnection()
        now_time = int(time.time())
        return self.client.get_logger(now_time - time_in_seconds, now_time)

    def validateConnection(self):
        if self.client.check_connection() is False:
            logging.error("SMA interface connection check failed")
            self.client = self.initConnection()

    def __del__(self):
        self.client.logout()


if __name__ == "__main__":
    smaInterface = SMAInterface()
    print(f"SMA power: {smaInterface.getCurrentPower()}")
    print(f"SMA keys: {smaInterface.client.get_all_keys()}")
