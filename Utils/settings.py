import os
import configparser
import serial
from DataHolder.buffer_attrs import Persistency, LifeSpan


class Settings:
    """Betrekt configuratie-instellingen uit config.ini"""

    def __init__(self):
        self.config = configparser.ConfigParser()
        currDir = os.path.dirname(os.path.dirname(__file__))
        configFilePath = os.path.join(currDir, 'config.ini')
        self.config.read(configFilePath)

    def smaHostname(self):
        return self.config.get('CONNECTION', 'sma_host')

    def smaPassword(self):
        return self.config.get('CONNECTION', 'sma_pwd')

    def webServerPort(self):
        return int(self.config.get('WEBSERVER', 'port'))

    def rs232Port(self):
        return self.config.get('RS232', 'port')

    def rs232Parity(self):
        return eval(self.config.get('RS232', 'parity'))

    def rs232Baud(self):
        return int(self.config.get('RS232', 'baudrate'))

    def rs232Stopbits(self):
        return eval(self.config.get('RS232', 'stopbits'))

    def rs232Bytesize(self):
        return eval(self.config.get('RS232', 'bytesize'))

    def get_data_stores(self) -> list[str]:
        return self.config.get('DATARETRIEVAL', 'data_stores').split()

    def get_data_store_name(self, data_store_id) -> str:
        return self.config.get('DATARETRIEVAL', data_store_id + '_name')

    def get_data_store_persistency(self, data_store_id) -> Persistency:
        return Persistency.Persistent if self.config.get('DATARETRIEVAL', data_store_id + '_persistency') == "persistent" \
            else Persistency.Volatile

    def get_data_store_lifespan(self, data_store_id) -> LifeSpan:
        return LifeSpan.Circular if self.config.get('DATARETRIEVAL', data_store_id + '_lifespan') == "circular" \
            else LifeSpan.Linear

    def get_data_store_signals(self, data_store_id) -> list[str]:
        return self.config.get('DATARETRIEVAL', data_store_id + '_signals').split()

    def get_data_store_buflen(self, data_store_id) -> int:
        return eval(self.config.get('DATARETRIEVAL', data_store_id + '_buflen'))

    def get_data_store_db(self, data_store_id) -> str:
        return self.config.get('DATARETRIEVAL', data_store_id + '_db')

    def persist_interval_minutes(self):
        return int(self.config.get('SCHEDULER', 'persist_interval_minutes'))

    def persist_delay_minutes(self):
        return int(self.config.get('SCHEDULER', 'persist_delay_minutes'))

    def data_dir_name(self):
        return self.config.get('PATHS', 'data')

    def db_filename(self):
        return self.config.get('PATHS', 'db_file')

    def logging_path(self):
        return self.config.get('PATHS', 'logging')

    def logging_filename(self):
        return self.config.get('PATHS', 'logfile')

