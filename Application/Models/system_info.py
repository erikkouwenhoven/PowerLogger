import os
import psutil
from datetime import datetime
from Application.inquirer import Inquirer
from DataHolder.db_interface import DBInterface


class SystemInfo:

    def __init__(self, inquirer: Inquirer):
        self.inquirer = inquirer
        self.info = self.get_info()

    def get_info(self) -> dict[str, str]:
        info = self.get_general_info()
        info = dict(info, **self.get_sys_info())
        info = dict(info, **self.get_app_info())
        return info

    def get_general_info(self) -> dict[str, str]:
        return {
            "Time start logging": str(self.inquirer.get_P1_start_time()),
            "Meter clock": str(self.inquirer.get_P1_clock()),
            "Server clock": str(datetime.now())
        }

    @staticmethod
    def get_sys_info() -> dict[str, str]:
        return {
            "Number of CPUs": psutil.cpu_count(),
            "CPU frequency": psutil.cpu_freq().current,
            "CPU temperature": SystemInfo.get_cpu_temp(),
            "CPU usage": psutil.cpu_times_percent().user,
            "CPU idle": psutil.cpu_times_percent().idle,
            "Total memory (MB)": psutil.virtual_memory().total / 1e6,
            "Memory in use (%)": psutil.virtual_memory().percent,
            "Boot time": str(datetime.fromtimestamp(psutil.boot_time())),
        }

    @staticmethod
    def get_app_info() -> dict[str, str]:
        return {
            "Database": DBInterface.db_file_name(),
            "Size of database (bytes)": os.path.getsize(DBInterface.db_file_name()),
        }

    @staticmethod
    def get_cpu_temp():
        try:
            res = psutil.sensors_temperatures()
            for key in res:
                return res[key][0].current
        except AttributeError:
            return None  # On Windows the function sensors_temperatures is non existent
