import time
import logging
from enum import Enum, auto
from SMASystem.sma import WebConnect
from SMASystem.key import Key
from SMASystem.right import Right
from Utils.settings import Settings


"""
    https://github.com/Dymerz/SMA-SunnyBoy
    https://sma-sunnyboy.readthedocs.io/en/latest/sma_sunnyboy.html
"""


class SMADataType(Enum):

    SOLAR = auto()


class SMAInterface:
    """
        Interface to the SMA Sunny Boy web server.
    """

    c_POWER_UNIT = 'W'

    def __init__(self):
        self.client = self.init_connection()

    @staticmethod
    def init_connection():
        client = WebConnect(Settings().sma_hostname(), Right.USER, Settings().sma_password())
        result = client.auth()
        if result is True:
            logging.info(f"Initializing connection to SMA Interface: success")
            return client
        else:
            logging.warning("Failed to initialize SMA interface")

    def get_current_power(self):
        self.validate_connection()
        if self.client:
            return self.client.get_value(Key.power_current)

    def get_total(self):
        self.validate_connection()
        if self.client:
            return self.client.get_value(Key.productivity_total)

    def get_history(self, time_in_seconds):
        self.validate_connection()
        if self.client:
            now_time = int(time.time())
            return self.client.get_logger(now_time - time_in_seconds, now_time)

    def validate_connection(self):
        if self.client:
            if self.client.check_connection() is False:
                logging.error("SMA interface connection check failed")
                self.client = self.init_connection()
        else:
            self.client = self.init_connection()

    def __del__(self):
        if self.client:
            self.client.logout()


if __name__ == "__main__":
    smaInterface = SMAInterface()
    print(f"SMA power: {smaInterface.get_current_power()}")
    print(f"SMA keys: {smaInterface.client.get_all_keys()}")
