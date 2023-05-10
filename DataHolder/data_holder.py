import logging
from Utils.settings import Settings
from DataHolder.circ_buffer import CircularMemBuf, CircularPersistentStorage
from DataHolder.db_interface import DBInterface
from P1System.data_classes import P1Sample, P1Value
from P1System.data_classes import DataType
from SMASystem.sma_interface import SMAInterface


class DataHolder:

    def __init__(self):
        self.real_time_data = CircularMemBuf(Settings().real_time_buf_length(), Settings().real_time_signals())
        self.db_interface = DBInterface(Settings().persist_signals())
        self.persistent_data = CircularPersistentStorage(Settings().persist_buf_length(), Settings().persist_signals(), self.db_interface)

    def addMeasurement(self, p1_sample: P1Sample, solar_power: float):  # TODO aangeven dat dit exclusief voor de realtime data is
        solar_value = P1Value(DataType.SOLAR)
        solar_value.setValue(solar_power, unit=SMAInterface.c_POWER_UNIT)
        p1_sample.addValue(solar_value)
        data_item = self.real_time_data.create_data_item()
        print(f">>> addMeasurement: data_item = {data_item}")
        data_item = self.real_time_data.create_data_item().from_p1sample(p1_sample)
        print(f">>>>>> addMeasurement: data_item = {data_item}")
        self.real_time_data.add_data_item(data_item)

    def get_realtime_average(self, from_time, to_time, selected_signals):
        return self.real_time_data.average(from_time, to_time, selected_signals)

    def persist_realtime_average(self, sample):
        logging.debug(f"DataHolder.persist_realtime_average: about to call self.persistent_data.append")
        self.persistent_data.append(sample)

    def get_persistent_timerange(self):
        return self.persistent_data.timestamp_range()

    def get_realtime_timerange(self):
        return self.real_time_data.timestamp_range()
