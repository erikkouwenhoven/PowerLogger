from Application.inquirer import Inquirer
from Application.Models.shift_info import ShiftInfo
from Application.Models.system_info import SystemInfo


class RequestExecutor:

    def __init__(self, inquirer: Inquirer):
        self.inquirer = inquirer

    def get_raw(self):
        return self.inquirer.get_P1_interface().get_raw_lines()

    def get_realtime_datadump(self):
        return self.inquirer.data_holder.data_store('real_time').data.dump()

    def get_data(self, args):
        info_msg = "Usage: get_data?data_store_name=<>&signals=<,>"
        if dict_args := self.convert_args(args):
            try:
                data_store = self.inquirer.data_holder.data_store(dict_args['data_store_name'])
                signals = dict_args['signals'].split(',')
            except KeyError:
                return info_msg
            return data_store.data.serialize(signals)
        else:
            return info_msg

    def get_data_stores(self, *args):
        return {"data_stores": self.inquirer.data_holder.get_data_stores()}

    def get_data_store_info(self, data_store_name: str) -> dict[str, any]:
        return self.inquirer.data_holder.data_store(data_store_name).data_store_info()

    @staticmethod
    def get_shift_info( *args):
        shift_info = ShiftInfo()
        return {"shift signal": shift_info.signal_to_shift, "shift in seconds": shift_info.shift_in_seconds}

    def get_system_info(self, *args):
        return SystemInfo(self.inquirer).get_info()

    @staticmethod
    def convert_args(args: str) -> dict[str, str] | None:
        res = {}
        for item in args.split('&'):
            key_value = item.split('=')
            if len(key_value) != 2:
                return None
            res[key_value[0]] = key_value[1]
        return res
