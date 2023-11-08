import os
import configparser
import serial
from datetime import datetime
from DataHolder.buffer_attrs import Persistency, LifeSpan
from P1System.data_classes import P1DataType


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

    def get_measurement_p1_signals(self) -> list[P1DataType]:
        return self.config.get('DATARETRIEVAL', 'p1_signals').split()

    def get_data_stores(self): # -> list[str]:
        return self.config.get('DATARETRIEVAL', 'data_stores').split()

    def get_data_store_name(self, data_store_id) -> str:
        return self.config.get('DATARETRIEVAL', data_store_id + '_name')

    def get_data_store_persistency(self, data_store_id) -> Persistency:
        return Persistency.Persistent if self.config.get('DATARETRIEVAL', data_store_id + '_persistency') == "persistent" \
            else Persistency.Volatile

    def get_data_store_lifespan(self, data_store_id) -> LifeSpan:
        return LifeSpan.Circular if self.config.get('DATARETRIEVAL', data_store_id + '_lifespan') == "circular" \
            else LifeSpan.Linear

    def get_data_store_signals(self, data_store_id): # -> list[str]:
        return self.config.get('DATARETRIEVAL', data_store_id + '_signals').split()

    def get_data_store_buflen(self, data_store_id) -> int:
        return eval(self.config.get('DATARETRIEVAL', data_store_id + '_buflen'))

    def get_data_store_db(self, data_store_id) -> str:
        return self.config.get('DATARETRIEVAL', data_store_id + '_db')

    def scheduled_jobs(self): # -> list[str]:
        return self.config.get('SCHEDULER', 'scheduled_jobs').split()

    def interval_minutes(self, job_id) -> int:
        return int(self.config.get('SCHEDULER', job_id + '_interval_minutes'))

    def start_delay_minutes(self, job_id) -> int:
        parameter = self.config.get('SCHEDULER', job_id + '_start_delay_minutes')
        if parameter[0] == '@':
            hour_str, minute_str = parameter[1:].split(':')
            hour = int(hour_str) if hour_str else None
            minute = int(minute_str)
            curr_time = datetime.now()
            delay = minute - curr_time.minute if minute - curr_time.minute > 0 else minute - curr_time.minute + 60
            if hour:
                delay += 60 * (hour - curr_time.hour if hour - curr_time.hour > 0 else hour - curr_time.hour + 24)
            return delay
        else:
            return int(parameter)

    def source(self, job_id) -> str:
        return self.config.get('SCHEDULER', job_id + '_source')

    def destination(self, job_id) -> str:
        return self.config.get('SCHEDULER', job_id + '_destination')

    def data_dir_name(self):
        return self.config.get('PATHS', 'data')

    def db_filename(self):
        return self.config.get('PATHS', 'db_file')

    def logging_path(self):
        return self.config.get('PATHS', 'logging')

    def logging_filename(self):
        return self.config.get('PATHS', 'logfile')

    def get_shift_in_seconds(self):
        return float(self.config.get('PROCESSING', 'shift_in_seconds'))

    def get_signal_to_shift(self) -> str:
        return self.config.get('PROCESSING', 'signal_to_shift')

    def get_config(self):
        if os.name == 'nt':
            return self.config.get('ZWAVE', 'configpath_windows')
        else:
            return self.config.get('ZWAVE', 'configpath_linux')

    def get_device(self):
        if os.name == 'nt':
            return self.config.get('ZWAVE', 'device_windows')
        else:
            return self.config.get('ZWAVE', 'device_linux')
