import os
import psutil
from datetime import datetime
from Application.processor import Processor
from DataHolder.db_interface import DBInterface


class SystemInfo:

    def __init__(self, processor: Processor):
        self.processor = processor
        self.info = self.get_info()

    def get_info(self) -> dict[str, str]:
        info = self.get_general_info()
        info = info | self.get_sys_info()
        info = info | self.get_app_info()
        return info

    def get_general_info(self) -> dict[str, str]:
        return {
            "Time start logging": str(self.processor.get_P1_start_time()),
            "Meter clock": str(self.processor.get_P1_clock()),
            "Server clock": str(datetime.now())
        }

    def get_sys_info(self) -> dict[str, str]:
        return {
            "Number of CPUs": psutil.cpu_count(),
            "CPU frequency": psutil.cpu_freq().current,
            "CPU temperature": self.get_cpu_temp(),
            "CPU usage": psutil.cpu_times_percent().user,
            "CPU idle": psutil.cpu_times_percent().idle,
            "Total memory (MB)": psutil.virtual_memory().total / 1e6,
            "Memory in use (%)": psutil.virtual_memory().percent,
            "Boot time": str(datetime.fromtimestamp(psutil.boot_time())),
        }

    def get_app_info(self) -> dict[str, str]:
        return {
            "Database": DBInterface.db_file_name(),
            "Size of database": os.path.getsize(DBInterface.db_file_name()),
        }

    @staticmethod
    def get_cpu_temp():
        res = psutil.sensors_temperatures()
        for key in res:
            return res[key][0].current
