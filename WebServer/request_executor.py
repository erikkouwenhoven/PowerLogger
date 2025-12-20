import logging
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
        if dict_args := self._convert_args(args):
            try:
                data_store = self.inquirer.data_holder.data_store(dict_args['data_store_name'])
                try:
                    signals = dict_args['signals'].split(',')
                    if signals == '*':
                        signals = None
                except KeyError:
                    signals = None
            except KeyError:
                return None
            return data_store.data.serialize(signals, human_readable=human_readable)
        else:
            return None

    def get_data_stores(self, *args):
        return {"data_stores": self.inquirer.data_holder.get_data_stores()}

    def get_data_store_info(self, data_store_name: str) -> dict[str, any]:
        return self.inquirer.data_holder.data_store(data_store_name).data_store_info()

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
