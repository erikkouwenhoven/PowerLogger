import logging
from typing import Any
from Utils.settings import Settings
from Application.inquirer import Inquirer
from WebServer.Forms.home_form import HomeForm
from Application.Models.system_info import SystemInfo


class RequestExecutor:

    def __init__(self, inquirer: Inquirer):
        self.inquirer = inquirer
        self.info_msg: str | None = None

    def home(self, args):
        home_form = HomeForm(self.inquirer)
        return home_form.render()

    def get_raw(self):
        return self.inquirer.get_P1_interface().get_raw_lines()

    def get_readable_data(self, args):
        return self.get_data(args, human_readable=True)

    def get_compact_data(self, args):
        return self.get_data(args, human_readable=False)

    def get_data(self, args, human_readable) -> dict | None:
        self.info_msg = "Usage: get_data?data_store_name=<> or get_data?data_store_name=<>&signals=<,>"
        if (dict_args := self._convert_args(args)) is None:
            logging.error(f"get_data: Could not convert args {args}")
            return None
        try:
            if (data_store := self.inquirer.data_holder.data_store(dict_args['data_store_name'])) is None:
                logging.error(f"get_data: Could not obtain data store {dict_args['data_store_name']}")
                return None
            try:
                signal_args = dict_args['signals'].split(',')
                signals = None if signal_args == '*' else signal_args
            except KeyError:
                signals = None
            if data_store.data is None:
                logging.error(f"get_data: No data in data store {data_store.name}")
                return None
            return data_store.data.serialize(signals, human_readable=human_readable)
        except KeyError:
            logging.error(f"get_data: Error in arguments: {dict_args}")
            return None

    def get_data_stores(self, *args) -> dict[str, list[str]]:
        return {"data_stores": self.inquirer.data_holder.get_data_stores()}

    def get_data_store_info(self, data_store_name: str) -> dict[str, Any] | None:
        if data_store := self.inquirer.data_holder.data_store(data_store_name):
            return data_store.data_store_info()
        else:
            return None

    @staticmethod
    def get_shift_info(*args):
        return {"shift in seconds": Settings().get_shift_in_seconds()}

    def get_system_info(self, *args):
        return SystemInfo(self.inquirer).get_info()

    @staticmethod
    def _convert_args(args: str) -> dict[str, str] | None:
        """
        Convert argument string used in url such as a=1&b=2&c=3 to dict such as {a:1, b:2, c:3}
        """
        res = {}
        for item in args.split('&'):
            key_value = item.split('=')
            if len(key_value) != 2:
                return None
            res[key_value[0]] = key_value[1]
        return res
