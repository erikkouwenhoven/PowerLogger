import logging
from datetime import datetime, timedelta
from P1System.p1_interface import P1Interface
from SMASystem.sma_interface import SMAInterface, SMADataType
from DataHolder.shift_info import ShiftInfo
from DataHolder.data_holder import DataHolder
from DataHolder.circ_buffer import DataItem
from Utils.settings import Settings


class Processor:
    """
        Initializes scheduled events, and receives and handles events.
    """

    c_PERSIST_JOB_ID = 'persist'

    def __init__(self, p1_interface: P1Interface, sma_interface: SMAInterface, data_holder: DataHolder):
        self.p1_interface = p1_interface
        self.sma_interface = sma_interface
        self.data_holder = data_holder

    def p1SampleAcquired(self):
        p1_sample = self.p1_interface.getSample()
        solar_power = self.sma_interface.getCurrentPower()
        data_item = DataItem.from_p1sample(p1_sample)
        if data_item:
            data_item.add_value(SMADataType.SOLAR.name, solar_power, SMAInterface.c_POWER_UNIT)
            self.data_holder.addMeasurement('real_time', data_item)

    def transfer_derived_value(self, source: str, dest: str, interval: timedelta):
        source_timerange = self.data_holder.get_timerange(source)
        start_timestamp = datetime.timestamp(datetime.fromtimestamp(source_timerange[1]) - interval)
        end_timestamp = source_timerange[1]
        if start_timestamp < source_timerange[0]:
            start_timestamp = source_timerange[0]

        start_time = datetime.fromtimestamp(start_timestamp)
        end_time = datetime.fromtimestamp(end_timestamp)
        logging.debug(f"Time range for persistent value calculation: {start_time} > {end_time}")
        shift_info = ShiftInfo()
        shift_info.set_sampling_time(self.p1_interface.get_sampling_period())
        avg = self.data_holder.get_average(source, start_time, end_time, self.data_holder.data_store(dest).signals, shift_info)
        logging.debug(f"Average: {avg}")
        self.data_holder.addMeasurement(dest, avg)
