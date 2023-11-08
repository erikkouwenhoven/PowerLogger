import logging
from datetime import datetime, timedelta
from Utils.settings import Settings
from P1System.p1_interface import P1Interface
from SMASystem.sma_interface import SMAInterface, SMADataType
from Application.Models.shift_info import ShiftInfo
from DataHolder.data_holder import DataHolder
from DataHolder.storage import DataItem


class Processor:
    """
        Receives and handles events.
    """

    def __init__(self, p1_interface: P1Interface, sma_interface: SMAInterface, data_holder: DataHolder):
        self.p1_interface = p1_interface
        self.sma_interface = sma_interface
        self.data_holder = data_holder

    def p1SampleAcquired(self):
        p1_sample = self.p1_interface.getSample()

        solar_power = self.sma_interface.getCurrentPower()
        if data_item := DataItem.from_p1sample(p1_sample, Settings().get_data_store_signals('real_time')):
            data_item.add_value(SMADataType.SOLAR.name, solar_power, SMAInterface.c_POWER_UNIT)
            self.data_holder.addMeasurement('real_time', data_item)

        if data_item := DataItem.from_p1sample_extra_timestamp(p1_sample, "CUMULATIVE_GAS"):
            data_store = self.data_holder.data_store('gas_cum_temp')
            if data_store.data.last_time() != data_item.get_timestamp():
                data_store.data.append(data_item)
                self.data_holder.addMeasurement('gas_cum_temp', data_item)
                if prev_item := data_store.data.get_data_item(data_store.data.last_index(offset=1)):
                    delta = data_item.get_value("CUMULATIVE_GAS") - prev_item.get_value("CUMULATIVE_GAS")
                    data_item_spec = self.data_holder.data_store('gas_hourly').data.data_item_spec
                    data_item_spec.set_unit("USAGE_GAS", "m3/h")
                    delta_data_item = DataItem(data_item_spec, timestamp=prev_item.get_timestamp())
                    delta_data_item.set_value("USAGE_GAS", delta)
                    self.data_holder.addMeasurement('gas_hourly', delta_data_item)

    def transfer_derived_value(self, source: str, dest: str, interval: timedelta):
        if (source_timerange := self.data_holder.get_timerange(source)) is not None:
            start_timestamp = datetime.timestamp(datetime.fromtimestamp(source_timerange[1]) - interval)
            end_timestamp = source_timerange[1]
            if start_timestamp < source_timerange[0]:
                start_timestamp = source_timerange[0]

            start_time = datetime.fromtimestamp(start_timestamp)
            end_time = datetime.fromtimestamp(end_timestamp)
            logging.debug(f"Time range for persistent value calculation: {start_time} > {end_time}")
            shift_info = ShiftInfo()
            shift_info.set_sampling_time(self.p1_interface.get_sampling_period())
            avg_signals = [signal for signal in self.data_holder.data_store(dest).signals if signal != "CUMULATIVE_GAS"]
            derived_data_item = self.data_holder.get_average(source, start_time, end_time, avg_signals, shift_info)  # dit is een data-item
            logging.debug(f"Average: {derived_data_item}")
            self.data_holder.addMeasurement(dest, derived_data_item)

    def get_P1_start_time(self) -> datetime:
        return self.p1_interface.interpreter.start_time

    def get_P1_clock(self):
        p1_sample = self.p1_interface.getSample()
        return p1_sample.get_timestamp()
