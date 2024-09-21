import os
import configparser
from Utils.time_delay import time_delay_minutes
import serial
from DataHolder.buffer_attrs import Persistency, LifeSpan
from P1System.p1_data_classes import P1DataType
from Application.Models.operation import Operation


class Settings:
    """Betrekt configuratie-instellingen uit config.ini"""

    def __init__(self):
        self.config = configparser.ConfigParser()
        curr_dir = os.path.dirname(os.path.dirname(__file__))
        config_file_path = os.path.join(curr_dir, 'config.ini')
        self.config.read(config_file_path)

    def sma_hostname(self):
        return self.config.get('CONNECTION', 'sma_host')

    def sma_password(self):
        return self.config.get('CONNECTION', 'sma_pwd')

    def web_server_port(self):
        return int(self.config.get('WEBSERVER', 'port'))

    def rs232_port(self):
        if os.name == 'nt':
            return self.config.get('RS232', 'port_windows')
        else:
            return self.config.get('RS232', 'port_linux')

    def rs232_parity(self):
        return eval(self.config.get('RS232', 'parity'))

    def rs232_baud(self):
        return int(self.config.get('RS232', 'baudrate'))

    def rs232_stopbits(self):
        return eval(self.config.get('RS232', 'stopbits'))

    def rs232_bytesize(self):
        return eval(self.config.get('RS232', 'bytesize'))

    def get_measurement_p1_signals(self) -> list[P1DataType]:
        signals: list[str] = self.config.get('DATARETRIEVAL', 'p1_signals').split()
        return [P1DataType[signal] for signal in signals]

    def get_data_stores(self) -> list[str]:
        return self.config.get('DATASTORAGE', 'data_stores').split()

    def get_P1_data_store(self):
        return self.config.get('DATASTORAGE', 'p1_data_store')

    def get_SMA_data_store(self):
        return self.config.get('DATASTORAGE', 'sma_data_store')

    def get_ZWave_data_store(self) -> str:
        return self.config.get('DATASTORAGE', 'zwave_data_store')

    def get_data_store_name(self, data_store_id) -> str:
        return self.config.get('DATASTORAGE', data_store_id + '_name')

    def get_data_store_persistency(self, data_store_id) -> Persistency:
        return Persistency.Persistent if self.config.get('DATASTORAGE', data_store_id + '_persistency') == "persistent" \
            else Persistency.Volatile

    def get_data_store_lifespan(self, data_store_id) -> LifeSpan:
        return LifeSpan.Circular if self.config.get('DATASTORAGE', data_store_id + '_lifespan') == "circular" \
            else LifeSpan.Linear

    def get_data_store_sampling_time_minutes(self, data_store_id) -> int | None:
        try:
            return eval(self.config.get('DATASTORAGE', data_store_id + '_sampling_time_minutes'))
        except configparser.NoOptionError:
            return None

    def get_data_store_signals(self, data_store_id) -> list[str]:
        return self.config.get('DATASTORAGE', data_store_id + '_signals').split()

    def get_data_store_buflen(self, data_store_id) -> int:
        return eval(self.config.get('DATASTORAGE', data_store_id + '_buflen'))

    def get_data_store_db(self, data_store_id) -> str:
        return self.config.get('DATASTORAGE', data_store_id + '_db')

    def get_min_storage_time_diff_seconds(self) -> int:
        return int(self.config.get('DATASTORAGE', 'min_storage_time_diff_seconds'))

    def scheduled_jobs(self) -> list[str]:
        return self.config.get('SCHEDULER', 'scheduled_jobs').split()

    def interval_minutes(self, job_id) -> int:
        return eval(self.config.get('SCHEDULER', job_id + '_interval_minutes'))

    def start_at_time(self, job_id) -> int | None:
        """
        Optionele parameter, indien niet ingevuld wordt None geretourneerd.
        Geeft de tijd van de dag aan waarop de job moet starten in de vorm van hh:mm.
        Het deel hh is optioneel, indien weggelaten wordt er ieder uur gestart.
        Geeft de delay in minuten terug.
        """
        try:
            time_str = self.config.get('SCHEDULER', job_id + '_start_at_time')
        except configparser.NoOptionError:
            return None
        return time_delay_minutes(time_str)

    def sched_job_sources(self, job_id) -> list[str]:
        return self.config.get('SCHEDULER', job_id + '_sources').split()

    def sched_job_destination(self, job_id) -> str:
        return self.config.get('SCHEDULER', job_id + '_destination')

    def sched_job_operation(self, job_id) -> tuple[Operation, list[str]]:
        """
        Geeft een Operation en operand terug.
        De operand heeft de vorm:
        - lege lijst
        - lijst van signaalnamen
        - '*' ten teken dat alle signalen onderworpen dienen te worden aan de Operatie
        """
        res = self.config.get('SCHEDULER', job_id + '_operation').split()
        operation = Operation[res[0]]
        if len(res) <= 1:
            operand = []
        elif len(res) == 2:
            operand = [res[1]]
        else:
            operand = res[1:]
        return operation, operand

    def data_dir_name(self) -> str:
        return self.config.get('PATHS', 'data')

    def db_filename(self) -> str:
        return self.config.get('PATHS', 'db_file')

    def logging_path(self) -> str:
        return self.config.get('PATHS', 'logging')

    def logging_filename(self) -> str:
        return self.config.get('PATHS', 'logfile')

    def get_shift_in_seconds(self) -> float:
        return float(self.config.get('PROCESSING', 'shift_in_seconds'))

    def get_unit(self, signal: str) -> str:
        return self.config.get('PROCESSING', 'unit_' + signal)

    def get_config(self):
        if os.name == 'nt':
            return self.config.get('ZWAVE', 'configpath_windows')
        else:
            return self.config.get('ZWAVE', 'configpath_linux')

    def get_ZWave_logfile(self):
        return self.config.get('ZWAVE', 'logfile')

    def get_device(self):
        if os.name == 'nt':
            return self.config.get('ZWAVE', 'device_windows')
        else:
            return self.config.get('ZWAVE', 'device_linux')

    def get_zwave_subscriptions(self) -> dict[int, list[str]]:
        res = {}
        for subscr in self.config.get('ZWAVE', 'subscriptions').split('\n'):
            split_res = subscr.split(':')
            node = int(split_res[0])
            val_ids = [val for val in split_res[1].split(',')]
            res[node] = val_ids
        return res
