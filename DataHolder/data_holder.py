import logging
from Utils.settings import Settings
from DataHolder.circ_buffer import CircularBuffer
from DataHolder.db_interface import DBInterface
from P1System.data_classes import P1Sample, P1Value
from P1System.data_classes import DataType
from SMASystem.sma_interface import SMAInterface


class DataHolder:

    def __init__(self):
        self.real_time_data = CircularBuffer(Settings().real_time_buf_length(), Settings().real_time_signals())
        self.db_interface = DBInterface(Settings().persist_signals())

    def addMeasurement(self, p1_sample: P1Sample, solar_power: float):
        solar_value = P1Value(DataType.SOLAR)
        solar_value.setValue(solar_power, unit=SMAInterface.c_POWER_UNIT)
        p1_sample.addValue(solar_value)
        self.real_time_data.append(p1_sample)

