from typing import Any


class RequestHandler:

    def __init__(self, processor):
        self.processor = processor

    def getStr(self):
        return self.processor.data_holder.data_store('real_time').data.str_last()

    def getRaw(self):
        return self.processor.p1_interface.getRawLines()

    def getRealtimeDatadump(self):
        return self.processor.data_holder.data_store('real_time').data.dump()

    def get_data(self, data_store_name):
        data_store = self.processor.data_holder.data_store(data_store_name)
        return data_store.data.serialize()

    def get_data_stores(self, *args):
        return {"data_stores": self.processor.data_holder.get_data_stores()}

    def get_data_store_info(self, data_store_name: str) -> dict[str, Any]:
        return self.processor.data_holder.data_store(data_store_name).data_store_info()
