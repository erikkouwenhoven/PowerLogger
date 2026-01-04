from typing import Any
import logging
from datetime import datetime
from Utils.settings import Settings
from DataHolder.storage import CircularMemStorage, CircularPersistentStorage, LinearPersistentStorage
from DataHolder.db_interface import DBInterface, DBInterfaceFactory
from DataHolder.buffer_attrs import Persistency, LifeSpan
from DataHolder.data_store import DataStore


class DataHolder:
    """
    Class that maintains the various data stores, either volatile of persistent.
    """

    def __init__(self):
        self.data_stores: list[DataStore] = self.init_data_stores()

    def get_timerange(self, data_store_name: str) -> list[float] | None:
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
            db_id = Settings().get_data_store_db(data_store_id) if persistency == Persistency.Persistent else None
            data_store = DataStore(name=name, persistency=persistency, lifespan=lifespan, signals=signals,
                                   sampling_period=sampling_period, buf_len=buf_len, db_id=db_id)
            if persistency == Persistency.Persistent:
                db_interface = DBInterfaceFactory.get_db(Settings().get_db_specifier(db_id))
                db_interface.create_table(name, signals)
                if lifespan == LifeSpan.Circular:
                    data_store.data = CircularPersistentStorage(buf_len, signals, db_interface, table=name)
                elif lifespan == LifeSpan.Linear:
                    data_store.data = LinearPersistentStorage(signals, db_interface, table=name)
            elif persistency == Persistency.Volatile and lifespan == LifeSpan.Circular:
                data_store.data = CircularMemStorage(buf_len, signals)
            else:
                raise NotImplementedError
            data_stores.append(data_store)
        return data_stores

    def get_data_stores(self) -> list[str]:
        return [data_store.name for data_store in self.data_stores]

    def filter(self, specific_signals: list[str], requirements: dict[str, Any] | None = None) -> DataStore | None:
        """
        Geeft een datastore die aan de eisen voldoet:
            bevat de signalen in specific_signals
            voldoet aan requirements, een dict met optionele extra eisen
                Time_span: Period De gevraagde datastore omvat deze tijdsspanne
                Persistency: Persistency van de datastore
        """
        result: dict[DataStore, bool] = {}
        for data_store in self.data_stores:
            result[data_store] = True
            if all([specific_signal in data_store.signals for specific_signal in specific_signals]):
                if requirements:
                    if "Persistency" in requirements:
                        if data_store.persistency != requirements["Persistency"]:
                            result[data_store] = False
                    if "Time_span" in requirements:
                        if ts_range := data_store.data.timestamp_range():
                            if requirements["Time_span"].is_contained(timerange_secs = ts_range[1] - ts_range[0]) is False:
                                result[data_store] = False
                        else:
                            result[data_store] = False
            else:
                result[data_store] = False
        logging.debug(f"De volgende data stores: {[data_store.name for data_store in result if result[data_store]]} voldoen aan"
                      f"de eisen: bevat de signalen {specific_signals}, en verder nog {requirements}")
        for data_store in result:
            if result[data_store]:
                return data_store

    def get_db_interfaces(self) -> list[DBInterface]:
        result: list[DBInterface] = []
        for data_store in self.data_stores:
            if data_store.persistency == Persistency.Persistent:
                db_interface = getattr(data_store.data, "db_interface")
                if db_interface not in result:
                    result.append(db_interface)
        return result
