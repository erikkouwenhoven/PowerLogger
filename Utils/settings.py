import os
import configparser
from P1System.data_classes import DataType


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
        return self.config.get('RS232', 'parity')

    def rs232Baud(self):
        return int(self.config.get('RS232', 'baudrate'))

    def rs232Stopbits(self):
        return self.config.get('RS232', 'stopbits')

    def rs232Bytesize(self):
        return self.config.get('RS232', 'bytesize')

    def real_time_signals(self):
        return [DataType[name] for name in self.config.get('DATARETRIEVAL', 'real_time_signals').split()]

    def real_time_buf_length(self):
        return int(eval(self.config.get('DATARETRIEVAL', 'real_time_buf')))

    def persist_signals(self):
        return [DataType[name] for name in self.config.get('SCHEDULER', 'persist_signals').split()]

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

