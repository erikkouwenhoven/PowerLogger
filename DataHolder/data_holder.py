from datetime import datetime
from Utils.settings import Settings
from DataHolder.storage import CircularMemStorage, CircularPersistentStorage, LinearPersistentStorage
from DataHolder.db_interface import DBInterface
from DataHolder.buffer_attrs import Persistency, LifeSpan
from DataHolder.data_store import DataStore
from Utils.time_delay import Period


class DataHolder:
    """
    Class that maintains the various data stores, either volatile of persistent.
    """

    def __init__(self):
        self.data_stores: list[DataStore] = self.init_data_stores()

    def get_timerange(self, data_store_name: str):
        return self.data_store(data_store_name).data.timestamp_range()

    def get_begin_time(self, data_store_name: str) -> datetime | None:
        if time_range := self.get_timerange(data_store_name):
            return datetime.fromtimestamp(time_range[0])

    def get_end_time(self, data_store_name: str) -> datetime | None:
        if time_range := self.get_timerange(data_store_name):
            return datetime.fromtimestamp(time_range[1])

    def data_store(self, data_store_name: str) -> DataStore | None:
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
            sampling_period = Settings().get_data_store_sampling_period(data_store_id)
            db = Settings().get_data_store_db(data_store_id) if persistency == Persistency.Persistent else None
            data_store = DataStore(name=name, persistency=persistency, lifespan=lifespan, signals=signals,
                                   sampling_period=sampling_period, buf_len=buf_len, db=db)
            if persistency == Persistency.Persistent and lifespan == LifeSpan.Circular:
                db_interface = DBInterface(name, signals)
                data_store.data = CircularPersistentStorage(buf_len, signals, db_interface, table=name)
            elif persistency == Persistency.Volatile and lifespan == LifeSpan.Circular:
                data_store.data = CircularMemStorage(buf_len, signals)
            elif persistency == Persistency.Persistent and lifespan == LifeSpan.Linear:
                db_interface = DBInterface(name, signals)
                data_store.data = LinearPersistentStorage(signals, db_interface, table=name)
            else:
                raise NotImplementedError
            data_stores.append(data_store)
        return data_stores

    def get_data_stores(self) -> list[str]:
        return [data_store.name for data_store in self.data_stores]

    def filter(self, specific_signals: list[str], req_time_span: Period | None = None,
               req_persistency: Persistency | None = None) -> DataStore | None:
        for data_store in self.data_stores:
            if req_persistency is None or data_store.persistency == req_persistency:
                if all([specific_signal in data_store.signals for specific_signal in specific_signals]):
                    if req_time_span is None or ((ts_range := data_store.data.timestamp_range()) and req_time_span.is_contained(ts_range[1] - ts_range[0])):
                        return data_store
