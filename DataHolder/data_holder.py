import logging
from Utils.settings import Settings
from DataHolder.circ_buffer import CircularMemBuf, CircularPersistentStorage, DataItem
from DataHolder.db_interface import DBInterface
from DataHolder.buffer_attrs import Persistency, LifeSpan
from DataHolder.data_store import DataStore


class DataHolder:
    """
    Class that maintains the various data stores, either volatile of persistent.
    """

    def __init__(self):
        self.data_stores: list[DataStore] = self.init_data_stores()

    def addMeasurement(self, data_store_name: str, data_item: DataItem):
        self.data_store(data_store_name).data.add_data_item(data_item)

    def get_average(self, data_store_name: str, from_time, to_time, selected_signals):
        return self.data_store(data_store_name).data.average(from_time, to_time, selected_signals)

    def get_timerange(self, data_store_name: str):
        return self.data_store(data_store_name).data.timestamp_range()

    def data_store(self, data_store_name: str) -> DataStore:
        for data_store in self.data_stores:
            if data_store.name == data_store_name:
                return data_store

    def init_data_stores(self) -> list[DataStore]:
        data_stores = []
        data_store_ids = Settings().get_data_stores()
        for data_store_id in data_store_ids:
            name = Settings().get_data_store_name(data_store_id)
            persistency = Settings().get_data_store_persistency(data_store_id)
            lifespan = Settings().get_data_store_lifespan(data_store_id)
            signals = Settings().get_data_store_signals(data_store_id)
            buf_len = Settings().get_data_store_buflen(data_store_id) if lifespan == LifeSpan.Circular else 0
            db = Settings().get_data_store_db(data_store_id) if persistency == Persistency.Persistent else None
            data_store = DataStore(name=name, persistency=persistency, lifespan=lifespan, signals=signals, buf_len=buf_len, db=db)
            if persistency == Persistency.Persistent:
                db_interface = DBInterface(signals)
                data_store.data = CircularPersistentStorage(buf_len, signals, db_interface)
            else:
                data_store.data = CircularMemBuf(buf_len, signals)
            data_stores.append(data_store)
        return data_stores

    def get_data_stores(self) -> list[str]:
        return [data_store.name for data_store in self.data_stores]
