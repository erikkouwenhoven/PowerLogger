import logging
from datetime import datetime, timedelta
from P1System.p1_interface import P1Interface
from SMASystem.sma_interface import SMAInterface, SMADataType
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

    def do_persist(self, interval: timedelta):  # TODO naam moet anders: transfer_average
        # TODO werken met data_sources i.p.v. hardcoded persistent en real_time
        # Get the start time of the averaging interval
        logging.debug(f"get_persistent_timerange: {self.data_holder.get_timerange('persistent')}")

        if (persistent_timerange := self.data_holder.get_timerange('persistent')) is None:
            start_timestamp = datetime.timestamp(datetime.fromtimestamp(persistent_timerange[1]) - interval)
            end_timestamp = persistent_timerange[1]
            if start_timestamp < persistent_timerange[0]:
                start_timestamp = persistent_timerange[0]
        else:
            realtime_timerange = self.data_holder.get_timerange('real_time')
            start_timestamp = datetime.timestamp(datetime.fromtimestamp(realtime_timerange[1]) - interval)
            end_timestamp = realtime_timerange[1]
            if start_timestamp < realtime_timerange[0]:
                start_timestamp = realtime_timerange[0]

        start_time = datetime.fromtimestamp(start_timestamp)
        end_time = datetime.fromtimestamp(end_timestamp)
        logging.debug(f"Time range for persistent value calculation: {start_time} > {end_time}")
        avg = self.data_holder.get_average('real_time', start_time, end_time, self.data_holder.data_store('persistent').signals)
        logging.debug(f"Average: {avg}")
        self.data_holder.addMeasurement('persistent', avg)
