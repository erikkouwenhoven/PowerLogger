from typing import Any
from DataHolder.shift_info import ShiftInfo


class RequestHandler:

    def __init__(self, processor):
        self.processor = processor

    def getStr(self):
        return self.processor.data_holder.data_store('real_time').data.str_last()

    def getRaw(self):
        return self.processor.p1_interface.get_raw_lines()

    def getRealtimeDatadump(self):
        return self.processor.data_holder.data_store('real_time').data.dump()

    def get_data(self, args):
        dict_args = self.convert_args(args)
        data_store = self.processor.data_holder.data_store(dict_args['data_store_name'])
        signals = dict_args['signals'].split(',')
        # datatype_from_name
        return data_store.data.serialize(signals)

    def get_data_stores(self, *args):
        return {"data_stores": self.processor.data_holder.get_data_stores()}

    def get_data_store_info(self, data_store_name: str) -> dict[str, Any]:
        return self.processor.data_holder.data_store(data_store_name).data_store_info()

    def get_shift_info(self, *args):
        shift_info = ShiftInfo()
        return {"shift signal": shift_info.signal_to_shift, "shift in seconds": shift_info.shift_in_seconds}

    @staticmethod
    def convert_args(args: str) -> dict[str, str]:
        res = {}
        for item in args.split('&'):
            key_value = item.split('=')
            assert len(key_value) == 2
            res[key_value[0]] = key_value[1]
        return res
